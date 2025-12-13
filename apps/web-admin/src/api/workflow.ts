import client from './client';

// Types
export interface WorkflowStep {
  id: string;
  name: string;
  task_type: string;
  order: number;
  config: Record<string, any>;
  depends_on: string[];
  condition?: string;
}

export interface WorkflowTemplate {
  id: number;
  name: string;
  description?: string;
  category?: string;
  version: string;
  tags: string[];
  workflow_def: {
    name: string;
    description?: string;
    version: string;
    steps: WorkflowStep[];
  };
  created_by?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  usage_count: number;
}

export interface CreateWorkflowTemplateRequest {
  name: string;
  description?: string;
  category?: string;
  version?: string;
  tags?: string[];
  workflow_def: {
    name: string;
    description?: string;
    version: string;
    steps: WorkflowStep[];
  };
}

export interface UpdateWorkflowTemplateRequest {
  name?: string;
  description?: string;
  category?: string;
  version?: string;
  tags?: string[];
  workflow_def?: {
    name: string;
    description?: string;
    version: string;
    steps: WorkflowStep[];
  };
}

export interface WorkflowExecutionRequest {
  template_id: number;
  params?: Record<string, any>;
  priority?: number;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface WorkflowTaskStatus {
  task_id: number;
  step_id: string;
  step_name: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  created_at?: string;
  start_time?: string;
  end_time?: string;
  total_items: number;
  success_items: number;
  failed_items: number;
  error_message?: string;
}

export interface WorkflowStatus {
  workflow_id: string;
  template_name: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  created_at: string;
  started_at?: string;
  completed_at?: string;
  tasks: WorkflowTaskStatus[];
  progress_percentage: number;
}

export interface Schedule {
  id: number;
  name: string;
  template_id: number;
  cron_expression: string;
  timezone: string;
  params: Record<string, any>;
  is_enabled: boolean;
  max_instances: number;
  timeout_seconds: number;
  description?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
  last_run_at?: string;
  next_run_at?: string;
  run_count: number;
  success_count: number;
  failure_count: number;
}

export interface CreateScheduleRequest {
  name: string;
  template_id: number;
  cron_expression: string;
  timezone?: string;
  params?: Record<string, any>;
  is_enabled?: boolean;
  max_instances?: number;
  timeout_seconds?: number;
  description?: string;
}

export interface UpdateScheduleRequest {
  name?: string;
  description?: string;
  cron_expression?: string;
  timezone?: string;
  params?: Record<string, any>;
  is_enabled?: boolean;
  max_instances?: number;
  timeout_seconds?: number;
}

export interface SchedulePreview {
  cron_expression: string;
  timezone: string;
  next_runs: string[];
  total_count: number;
  preview_range: {
    start: string;
    end: string;
  };
}

export interface CronExpressionRequest {
  frequency: 'minutely' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom';
  interval?: number;
  specific_times?: string[];
  days_of_month?: number[];
  days_of_week?: string[];
  months?: string[];
  timezone?: string;
}

export interface CronExpressionResponse {
  cron_expression: string;
  description: string;
  next_runs: string[];
  timezone: string;
}

export interface SchedulerStatus {
  total_jobs: number;
  schedule_jobs: number;
  loaded_schedules: number;
  scheduler_state: number;
  active_schedule_jobs: Array<{
    id: string;
    next_run_time: string | null;
    trigger: string;
  }>;
}

// Workflow Template APIs
export const workflowApi = {
  // Templates
  getTemplates: async (params?: {
    page?: number;
    page_size?: number;
    category?: string;
    is_active?: boolean;
    search?: string;
  }) => {
    return client.get<{
      items: WorkflowTemplate[];
      total: number;
      page: number;
      size: number;
      pages: number;
    }>('/admin/crawler/workflow/templates', { params });
  },

  getTemplate: async (id: number) => {
    return client.get<WorkflowTemplate>(`/admin/crawler/workflow/templates/${id}`);
  },

  createTemplate: async (data: CreateWorkflowTemplateRequest) => {
    return client.post<WorkflowTemplate>('/admin/crawler/workflow/templates', data);
  },

  updateTemplate: async (id: number, data: UpdateWorkflowTemplateRequest) => {
    return client.put<WorkflowTemplate>(`/admin/crawler/workflow/templates/${id}`, data);
  },

  deleteTemplate: async (id: number) => {
    return client.delete<{ success: boolean; message: string }>(`/admin/crawler/workflow/templates/${id}`);
  },

  // Execution
  executeWorkflow: async (data: WorkflowExecutionRequest) => {
    return client.post<{
      workflow_id: string;
      template_id: number;
      status: string;
      created_at: string;
      task_count: number;
      completed_count: number;
      failed_count: number;
      running_count: number;
      pending_count: number;
    }>('/admin/crawler/workflow/execute', data);
  },

  getWorkflowStatus: async (workflowId: string) => {
    return client.get<WorkflowStatus>(`/admin/crawler/workflow/${workflowId}/status`);
  },

  pauseWorkflow: async (workflowId: string) => {
    return client.post<{ success: boolean; message: string }>(`/admin/crawler/workflow/${workflowId}/pause`);
  },

  resumeWorkflow: async (workflowId: string) => {
    return client.post<{ success: boolean; message: string }>(`/admin/crawler/workflow/${workflowId}/resume`);
  },

  cancelWorkflow: async (workflowId: string) => {
    return client.post<{ success: boolean; message: string }>(`/admin/crawler/workflow/${workflowId}/cancel`);
  },

  // Schedules
  getSchedules: async (params?: {
    page?: number;
    page_size?: number;
    template_id?: number;
    is_enabled?: boolean;
  }) => {
    return client.get<{
      items: Schedule[];
      total: number;
      page: number;
      size: number;
      pages: number;
    }>('/admin/crawler/workflow/schedules', { params });
  },

  getSchedule: async (id: number) => {
    return client.get<Schedule>(`/admin/crawler/workflow/schedules/${id}`);
  },

  createSchedule: async (data: CreateScheduleRequest) => {
    return client.post<Schedule>('/admin/crawler/workflow/schedules', data);
  },

  updateSchedule: async (id: number, data: UpdateScheduleRequest) => {
    return client.put<Schedule>(`/admin/crawler/workflow/schedules/${id}`, data);
  },

  deleteSchedule: async (id: number) => {
    return client.delete<{ success: boolean; message: string }>(`/admin/crawler/workflow/schedules/${id}`);
  },

  enableSchedule: async (id: number) => {
    return client.post<{ success: boolean; message: string }>(`/admin/crawler/workflow/schedules/${id}/enable`);
  },

  disableSchedule: async (id: number) => {
    return client.post<{ success: boolean; message: string }>(`/admin/crawler/workflow/schedules/${id}/disable`);
  },

  // Schedule tools
  previewSchedule: async (data: {
    cron_expression: string;
    timezone?: string;
    start_time?: string;
    end_time?: string;
  }) => {
    return client.post<SchedulePreview>('/admin/crawler/workflow/schedules/preview', data);
  },

  generateCronExpression: async (data: CronExpressionRequest) => {
    return client.post<CronExpressionResponse>('/admin/crawler/workflow/schedules/cron/generate', data);
  },

  getSchedulerStatus: async () => {
    return client.get<SchedulerStatus>('/admin/crawler/workflow/schedules/status');
  },
};