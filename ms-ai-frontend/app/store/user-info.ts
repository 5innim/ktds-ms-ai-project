import { defineStore } from 'pinia';

export const useUserInfoStore = defineStore('userInfoStore', { 
  state: () => ({                                           
    memberInfo: {
      id: null as number | null,
    }
  }),
  actions: {
    setMemberInfo(memberInfo: { id: number | null }) {
      this.memberInfo = memberInfo;
    }
  }
});