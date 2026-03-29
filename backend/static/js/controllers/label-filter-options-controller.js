import { Controller } from "../vendor/stimulus.js"

function normalizeLabelSlug(value) {
  return String(value || "").trim().toLowerCase()
}

function normalizeLabelSlugs(values) {
  const normalized = []
  const seen = new Set()

  values.forEach((rawValue) => {
    const value = normalizeLabelSlug(rawValue)
    if (!value || seen.has(value)) {
      return
    }

    seen.add(value)
    normalized.push(value)
  })

  return normalized
}

function buildSearchPreservingNonLabel(sourceParams, selectedLabels) {
  const nextParams = new URLSearchParams()

  sourceParams.forEach((value, key) => {
    if (key !== "label") {
      nextParams.append(key, value)
    }
  })

  normalizeLabelSlugs(selectedLabels).forEach((slug) => {
    nextParams.append("label", slug)
  })

  return nextParams.toString()
}

export default class extends Controller {
  static targets = ["list", "noMatch", "option", "searchInput", "showMore"]

  connect() {
    this.showAll = this.hasShowMoreTarget
      && this.showMoreTarget.getAttribute("data-expanded") === "true"

    this.reorderLabelRows()
    this.updateLabelListVisibility()
  }

  search() {
    this.updateLabelListVisibility()
  }

  toggleShowMore(event) {
    event.preventDefault()

    this.showAll = !this.showAll

    if (this.hasShowMoreTarget) {
      this.showMoreTarget.setAttribute(
        "data-expanded",
        this.showAll ? "true" : "false"
      )
    }

    this.updateLabelListVisibility()
  }

  toggleLabel(event) {
    event.preventDefault()

    const button = event.currentTarget
    const labelSlug = button.getAttribute("data-label-slug")

    if (!labelSlug) {
      return
    }

    if (this.isLabelSelected(button)) {
      this.mutateLabelQuery("remove", labelSlug)
      return
    }

    this.mutateLabelQuery("add", labelSlug)
  }

  get selectedLabels() {
    return normalizeLabelSlugs(
      new URLSearchParams(window.location.search).getAll("label")
    )
  }

  isLabelSelected(button) {
    const slug = normalizeLabelSlug(button.getAttribute("data-label-slug"))
    return this.selectedLabels.includes(slug)
  }

  mutateLabelQuery(action, labelSlug) {
    const params = new URLSearchParams(window.location.search)
    let selectedLabels = normalizeLabelSlugs(params.getAll("label"))

    if (action === "add") {
      selectedLabels = normalizeLabelSlugs(selectedLabels.concat([labelSlug]))
    } else if (action === "remove") {
      const normalizedSlug = normalizeLabelSlug(labelSlug)
      selectedLabels = selectedLabels.filter((slug) => slug !== normalizedSlug)
    } else if (action === "clear") {
      selectedLabels = []
    }

    const nextSearch = buildSearchPreservingNonLabel(params, selectedLabels)
    const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ""}${window.location.hash}`
    window.location.assign(nextUrl)
  }

  reorderLabelRows() {
    if (!this.hasListTarget || !this.optionTargets.length) {
      return
    }

    const buttonsBySlug = new Map()
    this.optionTargets.forEach((button) => {
      buttonsBySlug.set(
        normalizeLabelSlug(button.getAttribute("data-label-slug")),
        button
      )
    })

    const selected = []
    this.selectedLabels.forEach((slug) => {
      if (buttonsBySlug.has(slug)) {
        selected.push(buttonsBySlug.get(slug))
      }
    })

    const selectedSet = new Set(
      selected.map((button) =>
        normalizeLabelSlug(button.getAttribute("data-label-slug"))
      )
    )

    const rest = this.optionTargets
      .filter((button) => {
        const slug = normalizeLabelSlug(button.getAttribute("data-label-slug"))
        return !selectedSet.has(slug)
      })
      .sort((first, second) => {
        const firstName = String(
          first.getAttribute("data-label-name") || ""
        ).toLowerCase()
        const secondName = String(
          second.getAttribute("data-label-name") || ""
        ).toLowerCase()

        if (firstName < secondName) {
          return -1
        }
        if (firstName > secondName) {
          return 1
        }
        return 0
      })

    selected.concat(rest).forEach((button) => {
      this.listTarget.appendChild(button)
    })
  }

  updateLabelListVisibility() {
    const query = this.hasSearchInputTarget
      ? this.searchInputTarget.value.trim().toLowerCase()
      : ""

    let visibleCount = 0
    const hasHiddenRows = this.optionTargets.some((button) => {
      return button.getAttribute("data-label-default-hidden") === "true"
    })

    this.optionTargets.forEach((button) => {
      const labelName = String(
        button.getAttribute("data-label-name") || ""
      ).toLowerCase()
      const defaultHidden =
        button.getAttribute("data-label-default-hidden") === "true"
      const selected = this.isLabelSelected(button)
      const matchesQuery = !query || labelName.includes(query)

      let isVisible = matchesQuery
      if (!query && !this.showAll && defaultHidden && !selected) {
        isVisible = false
      }

      button.classList.toggle("d-none", !isVisible)
      if (isVisible) {
        visibleCount += 1
      }
    })

    if (this.hasNoMatchTarget) {
      this.noMatchTarget.classList.toggle(
        "d-none",
        !(query && visibleCount === 0)
      )
    }

    if (this.hasShowMoreTarget) {
      if (query) {
        this.showMoreTarget.classList.add("d-none")
      } else {
        this.showMoreTarget.classList.toggle("d-none", !hasHiddenRows)
        this.showMoreTarget.textContent = this.showAll
          ? "Show less"
          : "Show more"
      }
    }
  }
}
