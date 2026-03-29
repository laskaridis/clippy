import { Controller } from "../vendor/stimulus.js"

function getCookie(name) {
  let cookieValue = null

  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")

    for (let index = 0; index < cookies.length; index += 1) {
      const cookie = cookies[index].trim()
      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }

  return cookieValue
}

export default class extends Controller {
  static targets = ["deleteButton"]

  static values = {
    deleteUrl: String,
  }

  connect() {
    this.csrfToken = getCookie("csrftoken")
  }

  async delete(event) {
    event.preventDefault()

    if (!this.deleteUrlValue) {
      return
    }

    try {
      const response = await fetch(this.deleteUrlValue, {
        method: "DELETE",
        headers: {
          "X-CSRFToken": this.csrfToken,
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      })

      if (response.status === 204 || response.status === 200) {
        this.element.remove()
        return
      }

      if (response.status === 403) {
        window.alert("You are not allowed to delete this clip.")
        return
      }

      window.alert("Failed to delete clip.")
    } catch (_error) {
      window.alert("Failed to delete clip.")
    }
  }
}
