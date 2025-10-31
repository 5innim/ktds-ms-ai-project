export const updateEmailSub = async (managerId: number, repositoryId: number, emailSub: boolean) => {
  const { $fetchClient } = useNuxtApp() as unknown as { $fetchClient: (url: string, options: any) => Promise<any> }

  return await $fetchClient('/manager/' + managerId + '/repositories/' + repositoryId + '/email-sub', {
    method: 'PATCH',
    withCredentials: true,
    body: { emailSub }
  })
}