import ClipCardController from "./clip-card-controller.js"
import FilterDrawerController from "./filter-drawer-controller.js"
import FilterSidebarController from "./filter-sidebar-controller.js"
import FilterTriggerRowController from "./filter-trigger-row-controller.js"
import GlobalAuthQuickSearchController from "./global-auth-quick-search-controller.js"
import GlobalThemeToggleController from "./global-theme-toggle-controller.js"
import LabelFilterOptionsController from "./label-filter-options-controller.js"

const CONTROLLERS = [
  ["clip-card", ClipCardController],
  ["filter-drawer", FilterDrawerController],
  ["filter-sidebar", FilterSidebarController],
  ["filter-trigger-row", FilterTriggerRowController],
  ["global-auth-quick-search", GlobalAuthQuickSearchController],
  ["global-theme-toggle", GlobalThemeToggleController],
  ["label-filter-options", LabelFilterOptionsController],
]

export function registerControllers(application) {
  CONTROLLERS.forEach(function registerController([identifier, controller]) {
    application.register(identifier, controller)
  })
}
