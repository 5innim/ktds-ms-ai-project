import { useUserInfoStore } from '@/store/user-info';

export default defineNuxtRouteMiddleware((to, from) => {
    const userInfoStore = useUserInfoStore();
    console.log(userInfoStore.memberInfo)

    if (!userInfoStore.memberInfo.id) {
        return navigateTo('/auth/login'); // 로그인 페이지로 리디렉션
    }
})
