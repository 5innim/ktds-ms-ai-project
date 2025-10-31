import type { ComputedRef, MaybeRef } from 'vue'
export type LayoutKey = "go-back-layout" | "scroll-layout" | "transparent-header-layout"
declare module 'nuxt/app' {
  interface PageMeta {
    layout?: MaybeRef<LayoutKey | false> | ComputedRef<LayoutKey | false>
  }
}