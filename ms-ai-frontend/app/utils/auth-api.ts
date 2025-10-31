export const login = async (managerId: number) => {
  const { $fetchClient } = useNuxtApp() as unknown as { $fetchClient: (url: string, options: any) => Promise<any> }

  return await $fetchClient('/manager/find', {
    method: 'POST',
    withCredentials: true,
    body: { managerId },
  })
}