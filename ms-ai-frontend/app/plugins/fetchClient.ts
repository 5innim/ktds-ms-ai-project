export default defineNuxtPlugin((nuxtApp) => {
    const config = useRuntimeConfig();

    const refreshToken = async () => {
      try {
        console.log("[Refresh] Requesting new token");
        await $fetch("/refresh", {
          baseURL: config.public.baseUrl || "http://localhost:8080",
          method: "POST",
          credentials: "include", 
        });
        console.log("[Refresh] Success");
      } catch (refreshError) {
        console.error("[Refresh] Failed", refreshError);
        throw refreshError;
      }
    };
  
    const fetchClient = async (url: string, options: { 
      method?: "GET" | "POST" | "PUT" | "DELETE";
      withCredentials?: boolean;
      body?: any;
    }) => {
      const { method = "GET", withCredentials = false, body = null } = options;
  
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
  
      try {
        console.log(`[Request] ${method} ${url}`, { withCredentials, body });
  
        const response = await $fetch(url, {
          baseURL: config.public.baseUrl || "http://localhost:8080",
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined,
          credentials: withCredentials ? "include" : undefined,
        });
  
        console.log(`[Response] ${method} ${url}`, response);
        return response;
      } catch (error: any) {
        console.error(`[Error] ${method} ${url}`, error);
        console.log(error?.response)
        console.log(error?.response?._data?.code)
        if (error?.response?._data?.code === '401003') {
          console.warn(`[Interceptor] Detected 401003. Refreshing token...`);
          try {
            await refreshToken();
          
            return await await $fetch(url, {
              baseURL: config.public.baseUrl || "http://localhost:8080",
              method,
              headers,
              body: body ? JSON.stringify(body) : undefined,
              credentials: withCredentials ? "include" : undefined,
            });

          } catch (retryError) {
            console.error(`[Error] ${method} ${url}`, retryError);
            throw retryError;
          }
        }

        throw error;
      }
    };
  
    return {
      provide: {
        fetchClient,
      },
    };
  });