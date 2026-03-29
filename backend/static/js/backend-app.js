import { Application } from "./vendor/stimulus.js"
import { registerControllers } from "./controllers/index.js"

const existingApplication = window.ClippyBackendStimulus

if (!existingApplication) {
  const application = Application.start()
  registerControllers(application)
  window.ClippyBackendStimulus = application
}
