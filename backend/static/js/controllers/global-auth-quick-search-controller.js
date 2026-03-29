import { Controller } from "../vendor/stimulus.js"

const MIN_QUERY_LENGTH = 3
const MAX_QUERY_LENGTH = 50
const DEFAULT_DEBOUNCE_MS = 200

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;")
}

function renderHighlightedSnippet(value) {
  const escaped = escapeHtml(value || "")
  return escaped.replace(/&lt;b&gt;/g, "<b>").replace(/&lt;\/b&gt;/g, "</b>")
}

export default class extends Controller {
  static targets = ["input", "panel", "results", "resultsItems"]

  static values = {
    debounceMs: Number,
    endpoint: String,
  }

  connect() {
    this.activeIndex = -1
    this.requestTimer = null
    this.abortController = null
    this.lastRenderedQuery = ""
    this.boundHandleDocumentClick = this.handleDocumentClick.bind(this)
    document.addEventListener("click", this.boundHandleDocumentClick)
  }

  disconnect() {
    document.removeEventListener("click", this.boundHandleDocumentClick)
    this.clearPendingRequestTimer()
    this.abortInFlightRequest()
  }

  queueSearch() {
    const query = this.inputTarget.value

    this.clearPendingRequestTimer()

    if (!query) {
      this.abortInFlightRequest()
      this.lastRenderedQuery = ""
      this.resultsItemsTarget.innerHTML = ""
      this.closePanel()
      return
    }

    const validation = this.validateQuery(query)
    if (!validation.valid) {
      this.abortInFlightRequest()
      this.closePanel()
      return
    }

    this.requestTimer = window.setTimeout(() => {
      void this.fetchQuickSearch(validation.query)
    }, this.debounceInterval)
  }

  searchOnFocus() {
    const query = this.inputTarget.value
    if (!query) {
      return
    }

    const validation = this.validateQuery(query)
    if (!validation.valid) {
      this.closePanel()
      return
    }

    if (
      validation.query === this.lastRenderedQuery &&
      this.resultsItemsTarget.innerHTML.trim()
    ) {
      this.openPanel()
      return
    }

    void this.fetchQuickSearch(validation.query)
  }

  handleKeydown(event) {
    const items = this.resultItems
    if (!items.length) {
      if (event.key === "Escape") {
        this.closePanel()
      }
      return
    }

    if (event.key === "ArrowDown") {
      event.preventDefault()
      this.setActiveItem(this.activeIndex + 1)
      return
    }

    if (event.key === "ArrowUp") {
      event.preventDefault()
      this.setActiveItem(this.activeIndex - 1)
      return
    }

    if (event.key === "Enter") {
      if (this.activeIndex >= 0 && this.activeIndex < items.length) {
        event.preventDefault()
        window.location.href = items[this.activeIndex].getAttribute("href") || "#"
      }
      return
    }

    if (event.key === "Escape") {
      event.preventDefault()
      this.closePanel()
    }
  }

  handleResultsMousemove(event) {
    const option = event.target.closest("[data-result-item]")
    if (!option || !this.resultsItemsTarget.contains(option)) {
      return
    }

    this.setActiveItem(this.resultItems.indexOf(option))
  }

  handleDocumentClick(event) {
    if (!this.element.contains(event.target)) {
      this.closePanel()
    }
  }

  get debounceInterval() {
    return this.hasDebounceMsValue ? this.debounceMsValue : DEFAULT_DEBOUNCE_MS
  }

  get endpoint() {
    return this.hasEndpointValue
      ? this.endpointValue
      : "/api/clips/quick-search/"
  }

  get resultItems() {
    return Array.from(this.resultsItemsTarget.querySelectorAll("[data-result-item]"))
  }

  validateQuery(query) {
    const normalizedQuery = String(query || "").trim()

    if (normalizedQuery.length < MIN_QUERY_LENGTH) {
      return {
        valid: false,
        message: "Type at least 3 characters to search.",
      }
    }

    if (normalizedQuery.length > MAX_QUERY_LENGTH) {
      return {
        valid: false,
        message: "Search must be 50 characters or less.",
      }
    }

    return { valid: true, message: "", query: normalizedQuery }
  }

  clearActiveState() {
    this.resultItems.forEach((item) => {
      item.classList.remove("global-auth-quick-search__item--active")
      item.setAttribute("aria-selected", "false")
    })
  }

  setActiveItem(index) {
    const items = this.resultItems
    if (!items.length) {
      this.activeIndex = -1
      this.inputTarget.removeAttribute("aria-activedescendant")
      return
    }

    let normalizedIndex = index
    if (normalizedIndex < 0) {
      normalizedIndex = items.length - 1
    } else if (normalizedIndex >= items.length) {
      normalizedIndex = 0
    }

    this.clearActiveState()
    this.activeIndex = normalizedIndex
    const activeItem = items[this.activeIndex]
    activeItem.classList.add("global-auth-quick-search__item--active")
    activeItem.setAttribute("aria-selected", "true")
    this.inputTarget.setAttribute("aria-activedescendant", activeItem.id)
    activeItem.scrollIntoView({ block: "nearest" })
  }

  closePanel() {
    this.activeIndex = -1
    this.inputTarget.setAttribute("aria-expanded", "false")
    this.inputTarget.removeAttribute("aria-activedescendant")
    this.panelTarget.classList.add("d-none")
  }

  openPanel() {
    this.inputTarget.setAttribute("aria-expanded", "true")
    this.panelTarget.classList.remove("d-none")
  }

  clearPendingRequestTimer() {
    if (this.requestTimer !== null) {
      window.clearTimeout(this.requestTimer)
      this.requestTimer = null
    }
  }

  abortInFlightRequest() {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
  }

  async fetchQuickSearch(query) {
    this.abortInFlightRequest()
    this.abortController = new AbortController()

    try {
      const response = await window.fetch(
        `${this.endpoint}?q=${encodeURIComponent(query)}`,
        {
          method: "GET",
          credentials: "same-origin",
          signal: this.abortController.signal,
          headers: {
            Accept: "application/json",
          },
        }
      )

      if (!response.ok) {
        throw new Error("Quick search request failed.")
      }

      const payload = await response.json()
      this.activeIndex = -1
      this.renderResults(payload)
    } catch (error) {
      if (error && error.name === "AbortError") {
        return
      }

      this.resultsItemsTarget.innerHTML =
        '<div class="p-3 text-secondary">Unable to load quick search results.</div>'
      this.openPanel()
    }
  }

  renderResults(payload) {
    const hits = payload?.hits || { clips: [], labels: [], websites: [] }
    const total = typeof payload?.total === "number" ? payload.total : 0
    this.lastRenderedQuery = typeof payload?.query === "string" ? payload.query : ""
    this.resultsItemsTarget.innerHTML = ""

    if (total === 0) {
      this.resultsItemsTarget.innerHTML =
        '<div class="p-3 text-secondary">No results found.</div>'
      this.openPanel()
      return
    }

    this.resultsItemsTarget.innerHTML = [
      this.renderGroup(hits.clips, "clips"),
      this.renderGroup(hits.labels, "labels"),
      this.renderGroup(hits.websites, "websites"),
    ].join("")
    this.openPanel()
  }

  renderGroup(items, title) {
    if (!items || !items.length) {
      return ""
    }

    let groupHtml = '<div class="p-2 border-bottom">'
    groupHtml += `<div class="global-auth-quick-search__group-title quick-search-group-title">${title}</div>`

    items.forEach((item, index) => {
      let secondaryText = ""
      let tertiaryText = ""

      if (item.type === "clip") {
        secondaryText = item.snippet || item.url || ""
        tertiaryText = item.title || ""
      } else {
        secondaryText = `${item.clip_count} clips`
      }

      const label = item.title || item.name || item.url || "Result"
      const safeLabel = escapeHtml(label)
      const safeSecondaryText =
        item.type === "clip"
          ? renderHighlightedSnippet(secondaryText)
          : escapeHtml(secondaryText)
      const safeTertiaryText = escapeHtml(tertiaryText)
      const safeUrl = escapeHtml(item.url || "")
      const safeTargetUrl = escapeHtml(item.target_url || "#")
      const optionId = `quick-search-option-${title}-${index}-${Math.abs(label.length + index)}`

      groupHtml += `<a href="${safeTargetUrl}" id="${optionId}" class="global-auth-quick-search__item list-group-item list-group-item-action quick-search-item" role="option" aria-selected="false" data-result-item>`

      if (item.type === "clip") {
        groupHtml += `<div class="global-auth-quick-search__clip-headline fw-semibold quick-search-clip-headline">${safeSecondaryText}</div>`
        if (tertiaryText || item.url) {
          let clipMeta = tertiaryText ? safeTertiaryText : ""
          if (item.url) {
            clipMeta = clipMeta ? `${clipMeta} · ${safeUrl}` : safeUrl
          }
          groupHtml += `<div class="global-auth-quick-search__clip-meta quick-search-clip-meta">${clipMeta}</div>`
        }
      } else {
        groupHtml += `<div class="fw-semibold">${safeLabel}</div>`
        if (secondaryText) {
          groupHtml += `<div class="small text-secondary">${safeSecondaryText}</div>`
        }
      }

      groupHtml += "</a>"
    })

    groupHtml += "</div>"
    return groupHtml
  }
}
