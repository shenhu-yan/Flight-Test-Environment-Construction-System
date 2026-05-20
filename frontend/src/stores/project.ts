import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

interface Project {
  id: string
  name: string
  description?: string
  created_by?: string
  created_at?: string
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)

  async function fetchProjects() {
    const response = await api.get('/api/projects')
    projects.value = response.data.data
    if (projects.value.length > 0 && !currentProject.value) {
      currentProject.value = projects.value[0]
    }
  }

  async function createProject(name: string, description?: string) {
    const response = await api.post('/api/projects', { name, description })
    await fetchProjects()
    return response.data.data
  }

  async function deleteProject(projectId: string) {
    await api.delete(`/api/projects/${projectId}`)
    if (currentProject.value?.id === projectId) {
      currentProject.value = null
    }
    await fetchProjects()
  }

  function setCurrentProject(project: Project) {
    currentProject.value = project
  }

  return {
    projects,
    currentProject,
    fetchProjects,
    createProject,
    deleteProject,
    setCurrentProject
  }
})
