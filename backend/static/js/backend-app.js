import { Application } from "./vendor/stimulus.js"
import { registerControllers } from "./controllers/index.js"
import { startLegacyBackendBootstrap } from "./legacy-backend-bootstrap.js"

const existingApplication = window.ClippyBackendStimulus

if (existingApplication) {
  startLegacyBackendBootstrap()
} else {
  const application = Application.start()
  registerControllers(application)
  window.ClippyBackendStimulus = application
  startLegacyBackendBootstrap()
}
