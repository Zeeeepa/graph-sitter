import { useQuery } from 'react-query';

import ProjectCard from './ProjectCard';
import { dashboardApi } from '../services/api';
import { useDashboardStore } from '../store/dashboardStore';
import { Project } from '../types';

const { data: projectsData, isLoading, error } = useQuery(
  'projects',
  dashboardApi.getProjects,
  {
    onSuccess: (data: Project[]) => {
      setProjects(data);
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  }
);

return (
  <Grid container spacing={3}>
    {projects.map((project: Project) => (
      <Grid item xs={12} sm={6} md={4} lg={3} key={project.id}>
        <ProjectCard
          project={project}
          onPin={handlePin}
          onUnpin={handleUnpin}
        />
      </Grid>
    ))}
  </Grid>
);
