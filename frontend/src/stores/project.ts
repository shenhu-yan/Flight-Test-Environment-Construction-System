import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getProjects } from '../api/projects'
import type { Project } from '../types'

export const useProjectStore = defineStore('project', () => {
  const currentProject = ref<Project | null>(null)
  const projects = ref<Project[]>([])

  async function fetchProjects() {
    const res = await getProjects({ page: 1, page_size: 100 })
    const data = res.data.data
    projects.value = Array.isArray(data) ? data : (data?.data || [])
  }

  function switchProject(project: Project) {
    currentProject.value = project
    localStorage.setItem('currentProjectId', project.id)
  }

  function initFromStorage() {
    const id = localStorage.getItem('currentProjectId')
    if (id && projects.value.length) {
      const found = projects.value.find(p => p.id === id)
      if (found) currentProject.value = found
    }
  }

  return { currentProject, projects, fetchProjects, switchProject, initFromStorage }
})
