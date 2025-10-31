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

    const fetchClientFormData = async (url: string, options: {
        method?: "POST" | "PUT";
        withCredentials?: boolean;
        formData: FormData;
    }) => {
        const { method = "POST", withCredentials = false, formData } = options;

        try {
            console.log(`[FormData Request] ${method} ${url}`, { withCredentials, formData });

            let response = await fetch(`${config.public.baseUrl || "http://localhost:8080"}${url}`, {
                method,
                body: formData,
                credentials: withCredentials ? "include" : undefined,
            });

            if (!response.ok) {
                const errorBody = await response.clone().json().catch(() => null);
                if (errorBody?.code === '401003') {
                    console.warn(`[Interceptor] Detected 401003. Refreshing token...`);
                    await refreshToken();
                    response = await await fetch(`${config.public.baseUrl || "http://localhost:8080"}${url}`, {
                        method,
                        body: formData,
                        credentials: withCredentials ? "include" : undefined,
                    });
                }
            }

            console.log(`[FormData Response] ${method} ${url}`, response);
            return response;
        } catch (error: any) {
            console.error(`[FormData Error] ${method} ${url}`, error);
            throw error;
        }
    };

    return {
        provide: {
            fetchClientFormData,
        },
    };
});
