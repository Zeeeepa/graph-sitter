// Generate mock workflow events
const generateWorkflowEvents = () => {
  const events: any[] = []; // Explicitly type the events array

  projects.forEach(project => {
    if (project.plan?.tasks) {
      // ... existing logic ...
    }
  });

  return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime()).slice(0, 10);
};
