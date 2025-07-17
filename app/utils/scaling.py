"""
Horizontal scaling and distributed processing utilities.

This module provides features for horizontal scaling including distributed task processing,
service discovery, load distribution, and cluster coordination.
"""

import asyncio
import json
import hashlib
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import socket
import os
import threading
from concurrent.futures import ThreadPoolExecutor

from app.utils.logging import get_logger

logger = get_logger(__name__)


class NodeStatus(Enum):
    """Node status in the cluster."""
    STARTING = "starting"
    HEALTHY = "healthy"
    BUSY = "busy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SHUTDOWN = "shutdown"


class TaskStatus(Enum):
    """Distributed task status."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NodeInfo:
    """Information about a cluster node."""
    node_id: str
    hostname: str
    port: int
    status: NodeStatus
    last_heartbeat: datetime
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    max_tasks: int = 10
    capabilities: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_healthy(self) -> bool:
        """Check if node is healthy."""
        return self.status in [NodeStatus.HEALTHY, NodeStatus.BUSY]
    
    @property
    def load_factor(self) -> float:
        """Calculate node load factor (0.0 to 1.0)."""
        task_load = self.active_tasks / self.max_tasks if self.max_tasks > 0 else 1.0
        resource_load = (self.cpu_usage + self.memory_usage) / 200.0  # Both are percentages
        return min(1.0, max(task_load, resource_load))
    
    @property
    def is_available(self) -> bool:
        """Check if node can accept new tasks."""
        return self.is_healthy and self.active_tasks < self.max_tasks


@dataclass
class DistributedTask:
    """Distributed task definition."""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    created_at: datetime
    assigned_node: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    required_capabilities: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": self.payload,
            "created_at": self.created_at.isoformat(),
            "assigned_node": self.assigned_node,
            "status": self.status.value,
            "priority": self.priority,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "required_capabilities": list(self.required_capabilities)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DistributedTask':
        """Create task from dictionary."""
        return cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            payload=data["payload"],
            created_at=datetime.fromisoformat(data["created_at"]),
            assigned_node=data.get("assigned_node"),
            status=TaskStatus(data["status"]),
            priority=data.get("priority", 0),
            timeout=data.get("timeout"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            required_capabilities=set(data.get("required_capabilities", []))
        )


class ServiceRegistry:
    """Service discovery and registration."""
    
    def __init__(self):
        self._nodes: Dict[str, NodeInfo] = {}
        self._services: Dict[str, Set[str]] = {}  # service_name -> node_ids
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_timeout = 60.0  # seconds
    
    async def register_node(
        self,
        node_id: str,
        hostname: str,
        port: int,
        capabilities: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a node in the cluster."""
        async with self._lock:
            self._nodes[node_id] = NodeInfo(
                node_id=node_id,
                hostname=hostname,
                port=port,
                status=NodeStatus.STARTING,
                last_heartbeat=datetime.now(timezone.utc),
                capabilities=capabilities or set(),
                metadata=metadata or {}
            )
        
        logger.info(f"Node registered: {node_id} at {hostname}:{port}")
    
    async def update_heartbeat(
        self,
        node_id: str,
        status: NodeStatus,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
        active_tasks: int = 0
    ):
        """Update node heartbeat and status."""
        async with self._lock:
            if node_id in self._nodes:
                node = self._nodes[node_id]
                node.status = status
                node.last_heartbeat = datetime.now(timezone.utc)
                node.cpu_usage = cpu_usage
                node.memory_usage = memory_usage
                node.active_tasks = active_tasks
    
    async def unregister_node(self, node_id: str):
        """Unregister a node from the cluster."""
        async with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                
                # Remove from services
                for service_nodes in self._services.values():
                    service_nodes.discard(node_id)
        
        logger.info(f"Node unregistered: {node_id}")
    
    async def get_healthy_nodes(self) -> List[NodeInfo]:
        """Get list of healthy nodes."""
        async with self._lock:
            return [
                node for node in self._nodes.values()
                if node.is_healthy
            ]
    
    async def get_available_nodes(self, required_capabilities: Optional[Set[str]] = None) -> List[NodeInfo]:
        """Get list of nodes available for new tasks."""
        async with self._lock:
            available_nodes = []
            
            for node in self._nodes.values():
                if not node.is_available:
                    continue
                
                # Check capabilities
                if required_capabilities and not required_capabilities.issubset(node.capabilities):
                    continue
                
                available_nodes.append(node)
            
            # Sort by load factor (least loaded first)
            available_nodes.sort(key=lambda n: n.load_factor)
            return available_nodes
    
    async def get_node(self, node_id: str) -> Optional[NodeInfo]:
        """Get node information."""
        async with self._lock:
            return self._nodes.get(node_id)
    
    async def start_cleanup_task(self):
        """Start cleanup task for stale nodes."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup_task(self):
        """Stop cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Cleanup stale nodes."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._remove_stale_nodes()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _remove_stale_nodes(self):
        """Remove nodes that haven't sent heartbeat."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self._heartbeat_timeout)
        
        async with self._lock:
            stale_nodes = [
                node_id for node_id, node in self._nodes.items()
                if node.last_heartbeat < cutoff_time
            ]
            
            for node_id in stale_nodes:
                logger.warning(f"Removing stale node: {node_id}")
                del self._nodes[node_id]
                
                # Remove from services
                for service_nodes in self._services.values():
                    service_nodes.discard(node_id)


class TaskDistributor:
    """Distributes tasks across cluster nodes."""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self._pending_tasks: List[DistributedTask] = []
        self._assigned_tasks: Dict[str, DistributedTask] = {}
        self._completed_tasks: Dict[str, DistributedTask] = {}
        self._lock = asyncio.Lock()
        self._distribution_task: Optional[asyncio.Task] = None
        self._task_handlers: Dict[str, Callable] = {}
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register handler for a task type."""
        self._task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: int = 0,
        timeout: Optional[float] = None,
        required_capabilities: Optional[Set[str]] = None
    ) -> str:
        """Submit a task for distributed processing."""
        task = DistributedTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload,
            created_at=datetime.now(timezone.utc),
            priority=priority,
            timeout=timeout,
            required_capabilities=required_capabilities or set()
        )
        
        async with self._lock:
            self._pending_tasks.append(task)
            # Sort by priority (higher priority first)
            self._pending_tasks.sort(key=lambda t: t.priority, reverse=True)
        
        logger.info(f"Task submitted: {task.task_id} (type: {task_type})")
        return task.task_id
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a task."""
        async with self._lock:
            # Check pending tasks
            for task in self._pending_tasks:
                if task.task_id == task_id:
                    return task.status
            
            # Check assigned tasks
            if task_id in self._assigned_tasks:
                return self._assigned_tasks[task_id].status
            
            # Check completed tasks
            if task_id in self._completed_tasks:
                return self._completed_tasks[task_id].status
        
        return None
    
    async def start_distribution(self):
        """Start task distribution."""
        if self._distribution_task is None:
            self._distribution_task = asyncio.create_task(self._distribution_loop())
    
    async def stop_distribution(self):
        """Stop task distribution."""
        if self._distribution_task:
            self._distribution_task.cancel()
            try:
                await self._distribution_task
            except asyncio.CancelledError:
                pass
    
    async def _distribution_loop(self):
        """Main distribution loop."""
        while True:
            try:
                await asyncio.sleep(1)  # Check every second
                await self._distribute_pending_tasks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in distribution loop: {e}")
    
    async def _distribute_pending_tasks(self):
        """Distribute pending tasks to available nodes."""
        async with self._lock:
            if not self._pending_tasks:
                return
            
            # Get available nodes
            available_nodes = await self.service_registry.get_available_nodes()
            if not available_nodes:
                return
            
            # Distribute tasks
            tasks_to_assign = []
            
            for task in self._pending_tasks[:]:
                # Find suitable node
                suitable_nodes = [
                    node for node in available_nodes
                    if task.required_capabilities.issubset(node.capabilities)
                ]
                
                if not suitable_nodes:
                    continue
                
                # Select node with lowest load
                selected_node = min(suitable_nodes, key=lambda n: n.load_factor)
                
                # Assign task
                task.assigned_node = selected_node.node_id
                task.status = TaskStatus.ASSIGNED
                
                tasks_to_assign.append(task)
                self._pending_tasks.remove(task)
                self._assigned_tasks[task.task_id] = task
                
                # Update node load
                selected_node.active_tasks += 1
                available_nodes = [n for n in available_nodes if n.is_available]
                
                if not available_nodes:
                    break
            
            # Log assignments
            for task in tasks_to_assign:
                logger.info(f"Task assigned: {task.task_id} -> {task.assigned_node}")


class LoadBalancer:
    """Load balancer for distributing requests across nodes."""
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        self._algorithms = {
            "round_robin": self._round_robin,
            "least_connections": self._least_connections,
            "weighted_round_robin": self._weighted_round_robin,
            "least_loaded": self._least_loaded
        }
        self._current_index = 0
        self._lock = asyncio.Lock()
    
    async def select_node(
        self,
        algorithm: str = "least_loaded",
        required_capabilities: Optional[Set[str]] = None
    ) -> Optional[NodeInfo]:
        """Select a node for handling a request."""
        available_nodes = await self.service_registry.get_available_nodes(required_capabilities)
        
        if not available_nodes:
            return None
        
        if algorithm in self._algorithms:
            return await self._algorithms[algorithm](available_nodes)
        else:
            # Default to least loaded
            return await self._least_loaded(available_nodes)
    
    async def _round_robin(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Round-robin selection."""
        async with self._lock:
            node = nodes[self._current_index % len(nodes)]
            self._current_index += 1
            return node
    
    async def _least_connections(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Select node with least active connections."""
        return min(nodes, key=lambda n: n.active_tasks)
    
    async def _weighted_round_robin(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Weighted round-robin based on node capacity."""
        # Simple implementation - could be enhanced with actual weights
        weights = [n.max_tasks for n in nodes]
        total_weight = sum(weights)
        
        async with self._lock:
            cumulative_weight = 0
            index = self._current_index % total_weight
            
            for i, weight in enumerate(weights):
                cumulative_weight += weight
                if index < cumulative_weight:
                    self._current_index += 1
                    return nodes[i]
            
            # Fallback
            return nodes[0]
    
    async def _least_loaded(self, nodes: List[NodeInfo]) -> NodeInfo:
        """Select node with lowest load factor."""
        return min(nodes, key=lambda n: n.load_factor)


class ClusterManager:
    """Main cluster management coordinator."""
    
    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or self._generate_node_id()
        self.service_registry = ServiceRegistry()
        self.task_distributor = TaskDistributor(self.service_registry)
        self.load_balancer = LoadBalancer(self.service_registry)
        self._initialized = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30.0  # seconds
    
    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        hostname = socket.gethostname()
        pid = os.getpid()
        timestamp = int(time.time())
        return f"{hostname}-{pid}-{timestamp}"
    
    async def initialize(
        self,
        hostname: str = "localhost",
        port: int = 8000,
        capabilities: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize cluster manager."""
        if self._initialized:
            return
        
        # Register this node
        await self.service_registry.register_node(
            node_id=self.node_id,
            hostname=hostname,
            port=port,
            capabilities=capabilities or {"general"},
            metadata=metadata or {}
        )
        
        # Start services
        await self.service_registry.start_cleanup_task()
        await self.task_distributor.start_distribution()
        
        # Start heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self._initialized = True
        logger.info(f"Cluster manager initialized for node: {self.node_id}")
    
    async def close(self):
        """Close cluster manager."""
        if not self._initialized:
            return
        
        # Stop heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Stop services
        await self.task_distributor.stop_distribution()
        await self.service_registry.stop_cleanup_task()
        
        # Unregister node
        await self.service_registry.unregister_node(self.node_id)
        
        self._initialized = False
        logger.info(f"Cluster manager closed for node: {self.node_id}")
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats."""
        while True:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                # Get current node status
                status = NodeStatus.HEALTHY  # Could be determined by health checks
                cpu_usage = 0.0  # Could be actual CPU usage
                memory_usage = 0.0  # Could be actual memory usage
                active_tasks = len(self.task_distributor._assigned_tasks)
                
                await self.service_registry.update_heartbeat(
                    node_id=self.node_id,
                    status=status,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    active_tasks=active_tasks
                )
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster statistics."""
        return {
            "node_id": self.node_id,
            "initialized": self._initialized,
            "total_nodes": len(self.service_registry._nodes),
            "healthy_nodes": len([
                n for n in self.service_registry._nodes.values()
                if n.is_healthy
            ]),
            "pending_tasks": len(self.task_distributor._pending_tasks),
            "assigned_tasks": len(self.task_distributor._assigned_tasks),
            "completed_tasks": len(self.task_distributor._completed_tasks)
        }


# Global cluster manager
_cluster_manager: Optional[ClusterManager] = None


def get_cluster_manager() -> ClusterManager:
    """Get global cluster manager."""
    global _cluster_manager
    if _cluster_manager is None:
        _cluster_manager = ClusterManager()
    return _cluster_manager


async def init_cluster_management(
    hostname: str = "localhost",
    port: int = 8000,
    capabilities: Optional[Set[str]] = None
):
    """Initialize global cluster management."""
    manager = get_cluster_manager()
    await manager.initialize(
        hostname=hostname,
        port=port,
        capabilities=capabilities or {"message_processing", "pdf_analysis", "openai_requests"}
    )
    return manager


async def cleanup_cluster_management():
    """Cleanup global cluster management."""
    global _cluster_manager
    if _cluster_manager:
        await _cluster_manager.close()
        _cluster_manager = None