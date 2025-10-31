export const registerToken = async (token: string) => {
  const { $fetchClient } = useNuxtApp() as unknown as { $fetchClient: (url: string, options: any) => Promise<any> }

  return await $fetchClient('/set-github-token', {
    method: 'POST',
    withCredentials: true,
    body: { token },
  })
}