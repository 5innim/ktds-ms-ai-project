export const getRepositories = async (managerId: number) => {
  const { $fetchClient } = useNuxtApp() as unknown as { $fetchClient: (url: string, options: any) => Promise<any> }

  return await $fetchClient('/repositories?manager_id=' + managerId, {
    method: 'GET',
    withCredentials: true,
    body: null
  })
}


export const getRepository = async (repositoryId: string, managerId: number) => {
  const { $fetchClient } = useNuxtApp() as unknown as { $fetchClient: (url: string, options: any) => Promise<any> }

  return await $fetchClient('/repositories/' + repositoryId + '?manager_id=' + managerId, {
    method: 'GET',
    withCredentials: true,
    body: null
  })
}

export const addAddressee = async (repositoryId: number, name: string, email: string) => {
  const { $fetchClient } = useNuxtApp() as unknown as { $fetchClient: (url: string, options: any) => Promise<any> }

  return await $fetchClient('/repositories/' + repositoryId + '/addressee', {
    method: 'POST',
    withCredentials: true,
    body: { name, email }
  })
}

export const deleteAddressee = async (repositoryId: number, email: string) => {
  const { $fetchClient } = useNuxtApp() as unknown as { $fetchClient: (url: string, options: any) => Promise<any> }

  return await $fetchClient('/repositories/' + repositoryId + '/addressees?email=' + email, {
    method: 'DELETE',
    withCredentials: true,
    body: null
  })
}