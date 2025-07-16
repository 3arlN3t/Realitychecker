import React from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardActions, 
  Button, 
  Divider,
  Tooltip
} from '@mui/material';
import { ReportTemplate } from './types';
import DescriptionIcon from '@mui/icons-material/Description';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

interface ReportTemplatesProps {
  templates: ReportTemplate[];
  onUseTemplate: (template: ReportTemplate) => void;
  onEditTemplate?: (template: ReportTemplate) => void;
  onDeleteTemplate?: (templateId: string) => void;
  onCreateTemplate?: () => void;
}

const ReportTemplates: React.FC<ReportTemplatesProps> = ({
  templates,
  onUseTemplate,
  onEditTemplate,
  onDeleteTemplate,
  onCreateTemplate
}) => {
  // Get icon component based on template type
  const getTemplateIcon = (template: ReportTemplate) => {
    return <span className="material-icons">{template.icon}</span>;
  };

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          <DescriptionIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Report Templates
        </Typography>
        {onCreateTemplate && (
          <Button 
            variant="outlined" 
            startIcon={<AddIcon />}
            onClick={onCreateTemplate}
          >
            Create Template
          </Button>
        )}
      </Box>
      
      <Typography variant="body2" color="textSecondary" paragraph>
        Use pre-configured report templates for common reporting needs
      </Typography>
      
      <Divider sx={{ my: 2 }} />
      
      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} sm={6} md={4} key={template.id}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  {getTemplateIcon(template)}
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    {template.name}
                  </Typography>
                </Box>
                <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                  {template.description}
                </Typography>
                <Typography variant="caption" display="block">
                  Report Type: {template.report_type}
                </Typography>
                {template.default_parameters.export_format && (
                  <Typography variant="caption" display="block">
                    Format: {template.default_parameters.export_format}
                  </Typography>
                )}
              </CardContent>
              <CardActions>
                <Button 
                  size="small" 
                  color="primary"
                  onClick={() => onUseTemplate(template)}
                >
                  Use Template
                </Button>
                {onEditTemplate && (
                  <Tooltip title="Edit Template">
                    <Button 
                      size="small"
                      onClick={() => onEditTemplate(template)}
                    >
                      <EditIcon fontSize="small" />
                    </Button>
                  </Tooltip>
                )}
                {onDeleteTemplate && (
                  <Tooltip title="Delete Template">
                    <Button 
                      size="small" 
                      color="error"
                      onClick={() => onDeleteTemplate(template.id)}
                    >
                      <DeleteIcon fontSize="small" />
                    </Button>
                  </Tooltip>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
        
        {templates.length === 0 && (
          <Grid item xs={12}>
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="textSecondary">
                No report templates available
              </Typography>
              {onCreateTemplate && (
                <Button 
                  variant="outlined" 
                  startIcon={<AddIcon />}
                  onClick={onCreateTemplate}
                  sx={{ mt: 2 }}
                >
                  Create Your First Template
                </Button>
              )}
            </Box>
          </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default ReportTemplates;