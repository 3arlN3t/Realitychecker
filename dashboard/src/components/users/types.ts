export interface UserInteraction {
  id: string;
  timestamp: string;
  messageType: 'text' | 'pdf';
  content: string;
  analysisResult?: {
    trustScore: number;
    classification: 'Legit' | 'Suspicious' | 'Likely Scam';
    reasons: string[];
  };
  responseTime: number;
  error?: string;
}

export interface UserDetails {
  id: string;
  phoneNumber: string;
  firstInteraction: string;
  lastInteraction: string;
  totalRequests: number;
  blocked: boolean;
  interactionHistory: UserInteraction[];
  engagementScore: number;
  averageResponseTime: number;
  mostFrequentHour: number;
}

export interface UserSearchProps {
  onSearch: (query: string) => void;
  searchQuery: string;
}

export interface UserTableProps {
  users: UserDetails[];
  onBlockUser: (userId: string) => void;
  onUnblockUser: (userId: string) => void;
  onUserSelect: (user: UserDetails) => void;
  page: number;
  rowsPerPage: number;
  onPageChange: (page: number) => void;
  onRowsPerPageChange: (rowsPerPage: number) => void;
}

export interface UserInteractionModalProps {
  user: UserDetails | null;
  open: boolean;
  onClose: () => void;
}