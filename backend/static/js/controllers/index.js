import clipCardController from "./clip-card-controller.js"
import filterDrawerController from "./filter-drawer-controller.js"
import filterSidebarController from "./filter-sidebar-controller.js"
import filterTriggerRowController from "./filter-trigger-row-controller.js"
import globalAuthQuickSearchController from "./global-auth-quick-search-controller.js"
import globalThemeToggleController from "./global-theme-toggle-controller.js"
import labelFilterOptionsController from "./label-filter-options-controller.js"

const CONTROLLERS = [
  ["clip-card", clipCardController],
  ["filter-drawer", filterDrawerController],
  ["filter-sidebar", filterSidebarController],
  ["filter-trigger-row", filterTriggerRowController],
  ["global-auth-quick-search", globalAuthQuickSearchController],
  ["global-theme-toggle", globalThemeToggleController],
  ["label-filter-options", labelFilterOptionsController],
]

export function registerControllers(application) {
  CONTROLLERS.forEach(function registerController([identifier, controller]) {
    application.register(identifier, controller)
  })
}
