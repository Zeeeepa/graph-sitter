/**
 * Plan Creator Component - AI-powered plan generation and management
 */
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  TextField,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  AutoAwesome,
  Edit,
  Save,
  PlayArrow,
  Visibility,
  Code,
  CloudUpload,
  Security,
  Timeline,
  CheckCircle,
  Schedule,
  Refresh,
} from '@mui/icons-material';

import { apiService } from '../services/api';

const PlanCreator = ({ project, sx }) => {
  const [requirements, setRequirements] = useState(project?.requirements || '');
  const [plan, setPlan] = useState(project?.plan || '');
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [planPreviewOpen, setPlanPreviewOpen] = useState(false);
  const [planSteps, setPlanSteps] = useState([]);

  useEffect(() => {
    if (project) {
      setRequirements(project.requirements || '');
      setPlan(project.plan || '');
      
      // Parse existing plan if available
      if (project.plan) {
        parsePlanSteps(project.plan);
      }
    }
  }, [project]);

  const parsePlanSteps = (planText) => {
    // Simple plan parsing - in a real implementation, this would be more sophisticated
    const lines = planText.split('\n').filter(line => line.trim());
    const steps = [];
    
    lines.forEach((line, index) => {
      if (line.match(/^\d+\./)) {
        const stepText = line.replace(/^\d+\.\s*/, '');
        const stepType = detectStepType(stepText);
        
        steps.push({
          id: `step_${index}`,
          name: stepText,
          type: stepType,
          status: 'pending',
          description: stepText
        });
      }
    });
    
    setPlanSteps(steps);
  };

  const detectStepType = (stepText) => {
    const text = stepText.toLowerCase();
    
    if (text.includes('analyz') || text.includes('review') || text.includes('check')) {
      return 'code_analysis';
    } else if (text.includes('deploy') || text.includes('release')) {
      return 'deployment';
    } else if (text.includes('test') || text.includes('validat')) {
      return 'validation';
    } else if (text.includes('pr') || text.includes('pull request') || text.includes('merge')) {
      return 'pr_creation';
    } else if (text.includes('agent') || text.includes('ai') || text.includes('generate')) {
      return 'agent_execution';
    } else {
      return 'general';
    }
  };

  const handleGeneratePlan = async () => {
    if (!requirements.trim()) {
      return;
    }

    try {
      setLoading(true);
      
      // Use Codegen agent to generate plan
      const response = await apiService.executeAgent(
        `Create a detailed execution plan for the following requirements: ${requirements}`,
        project.id
      );
      
      // Wait for agent completion
      let taskStatus = response;
      while (taskStatus.status === 'running' || taskStatus.status === 'pending') {
        await new Promise(resolve => setTimeout(resolve, 2000));
        taskStatus = await apiService.getAgentStatus(response.task_id);
      }
      
      if (taskStatus.status === 'completed') {
        const generatedPlanText = taskStatus.result;
        setGeneratedPlan(generatedPlanText);
        setPlan(generatedPlanText);
        parsePlanSteps(generatedPlanText);
      } else {
        throw new Error('Plan generation failed');
      }
      
    } catch (error) {
      console.error('Error generating plan:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePlan = async () => {
    try {
      setSaving(true);
      
      await apiService.updateProject(project.id, {
        requirements,
        plan
      });
      
      // Update local project data
      project.requirements = requirements;
      project.plan = plan;
      
    } catch (error) {
      console.error('Error saving plan:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleStartWorkflow = async () => {
    try {
      setLoading(true);
      
      // Create workflow from plan
      const workflowData = {
        project_id: project.id,
        name: `AI Workflow - ${project.name}`,
        plan: plan,
        requirements: requirements
      };
      
      const workflow = await apiService.createWorkflow(workflowData);
      
      // Start the workflow
      await apiService.startWorkflow(workflow.workflow_id);
      
    } catch (error) {
      console.error('Error starting workflow:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStepIcon = (stepType) => {
    const icons = {
      code_analysis: <Code />,
      agent_execution: <AutoAwesome />,
      pr_creation: <Timeline />,
      deployment: <CloudUpload />,
      validation: <Security />,
      general: <Schedule />,
    };
    return icons[stepType] || <Schedule />;
  };

  const getStepColor = (stepType) => {
    const colors = {
      code_analysis: 'primary',
      agent_execution: 'secondary',
      pr_creation: 'info',
      deployment: 'warning',
      validation: 'success',
      general: 'default',
    };
    return colors[stepType] || 'default';
  };

  return (
    <Card sx={{ ...sx }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" component="div">
            ✨ AI Plan Creator
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {plan && (
              <Tooltip title="Preview Plan">
                <IconButton onClick={() => setPlanPreviewOpen(true)}>
                  <Visibility />
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title="Refresh">
              <IconButton onClick={() => window.location.reload()}>
                <Refresh />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Requirements Input */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Project Requirements
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="Describe what you want to achieve with this project..."
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            variant="outlined"
            sx={{ mb: 2 }}
          />
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <AutoAwesome />}
              onClick={handleGeneratePlan}
              disabled={!requirements.trim() || loading}
            >
              {loading ? 'Generating...' : 'Generate Plan'}
            </Button>
            
            {requirements !== project?.requirements && (
              <Button
                variant="outlined"
                startIcon={saving ? <CircularProgress size={20} /> : <Save />}
                onClick={handleSavePlan}
                disabled={saving}
              >
                Save Requirements
              </Button>
            )}
          </Box>
        </Box>

        {/* Generated Plan */}
        {plan && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Execution Plan
            </Typography>
            
            {generatedPlan && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Plan generated successfully! Review and edit if needed.
              </Alert>
            )}
            
            <TextField
              fullWidth
              multiline
              rows={8}
              value={plan}
              onChange={(e) => {
                setPlan(e.target.value);
                parsePlanSteps(e.target.value);
              }}
              variant="outlined"
              sx={{ mb: 2 }}
            />
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={<PlayArrow />}
                onClick={handleStartWorkflow}
                disabled={loading}
              >
                Start Workflow
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<Save />}
                onClick={handleSavePlan}
                disabled={saving || plan === project?.plan}
              >
                Save Plan
              </Button>
            </Box>
          </Box>
        )}

        {/* Plan Steps Preview */}
        {planSteps.length > 0 && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Plan Steps Preview
            </Typography>
            
            <Paper sx={{ p: 2, backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
              <Stepper orientation="vertical" activeStep={-1}>
                {planSteps.map((step, index) => (
                  <Step key={step.id}>
                    <StepLabel icon={getStepIcon(step.type)}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body1">
                          {step.name}
                        </Typography>
                        <Chip
                          label={step.type.replace('_', ' ')}
                          size="small"
                          color={getStepColor(step.type)}
                          variant="outlined"
                        />
                      </Box>
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2" color="textSecondary">
                        {step.description}
                      </Typography>
                    </StepContent>
                  </Step>
                ))}
              </Stepper>
            </Paper>
          </Box>
        )}

        {/* Empty State */}
        {!requirements && !plan && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <AutoAwesome sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Create Your AI-Powered Plan
            </Typography>
            <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
              Describe your project requirements and let AI generate a comprehensive execution plan
            </Typography>
            <Typography variant="body2" color="textSecondary">
              The plan will include code analysis, agent execution, PR creation, deployment, and validation steps
            </Typography>
          </Box>
        )}

        {/* Plan Preview Dialog */}
        <Dialog
          open={planPreviewOpen}
          onClose={() => setPlanPreviewOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            Plan Preview: {project?.name}
          </DialogTitle>
          <DialogContent>
            <Box>
              <Typography variant="h6" gutterBottom>
                Requirements
              </Typography>
              <Paper sx={{ p: 2, mb: 3, backgroundColor: 'rgba(0, 0, 0, 0.1)' }}>
                <Typography variant="body1">
                  {requirements || 'No requirements specified'}
                </Typography>
              </Paper>
              
              <Typography variant="h6" gutterBottom>
                Execution Plan
              </Typography>
              <Paper sx={{ p: 2, mb: 3, backgroundColor: 'rgba(0, 0, 0, 0.1)' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {plan || 'No plan generated'}
                </Typography>
              </Paper>
              
              {planSteps.length > 0 && (
                <>
                  <Typography variant="h6" gutterBottom>
                    Step Breakdown
                  </Typography>
                  <List>
                    {planSteps.map((step, index) => (
                      <React.Fragment key={step.id}>
                        <ListItem>
                          <ListItemIcon>
                            {getStepIcon(step.type)}
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body1">
                                  {step.name}
                                </Typography>
                                <Chip
                                  label={step.type.replace('_', ' ')}
                                  size="small"
                                  color={getStepColor(step.type)}
                                  variant="outlined"
                                />
                              </Box>
                            }
                            secondary={step.description}
                          />
                        </ListItem>
                        {index < planSteps.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </>
              )}
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setPlanPreviewOpen(false)}>Close</Button>
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={() => {
                setPlanPreviewOpen(false);
                handleStartWorkflow();
              }}
              disabled={!plan}
            >
              Start Workflow
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default PlanCreator;

