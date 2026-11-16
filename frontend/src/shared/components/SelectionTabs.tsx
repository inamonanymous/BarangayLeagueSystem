import { useId, useRef, type KeyboardEvent, type ReactNode } from 'react'

interface TabItem {
  id: number
  label: string
  content: ReactNode
}

interface SelectionTabsProps {
  label: string
  items: TabItem[]
  selectedId: number | null
  onSelect: (id: number) => void
}

export function selectedTabId(ids: number[], selectedId: number | null): number | undefined {
  return selectedId !== null && ids.includes(selectedId) ? selectedId : ids[0]
}

function SelectionTabs({ label, items, selectedId, onSelect }: SelectionTabsProps) {
  const prefix = useId()
  const tabs = useRef<(HTMLButtonElement | null)[]>([])
  const currentId = selectedTabId(items.map((item) => item.id), selectedId)

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index
    if (event.key === 'ArrowRight') next = (index + 1) % items.length
    else if (event.key === 'ArrowLeft') next = (index - 1 + items.length) % items.length
    else if (event.key === 'Home') next = 0
    else if (event.key === 'End') next = items.length - 1
    else return
    event.preventDefault()
    onSelect(items[next].id)
    tabs.current[next]?.focus()
  }

  if (!items.length) return null

  return (
    <div className="selection-tabs">
      <div className="selection-tabs__list" role="tablist" aria-label={label}>
        {items.map((item, index) => (
          <button
            key={item.id}
            ref={(element) => { tabs.current[index] = element }}
            type="button"
            role="tab"
            id={`${prefix}-tab-${item.id}`}
            aria-controls={`${prefix}-panel-${item.id}`}
            aria-selected={item.id === currentId}
            tabIndex={item.id === currentId ? 0 : -1}
            onClick={() => onSelect(item.id)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            {item.label}
          </button>
        ))}
      </div>
      {items.map((item) => (
        <div
          key={item.id}
          role="tabpanel"
          id={`${prefix}-panel-${item.id}`}
          aria-labelledby={`${prefix}-tab-${item.id}`}
          tabIndex={0}
          hidden={item.id !== currentId}
        >
          {item.content}
        </div>
      ))}
    </div>
  )
}

export default SelectionTabs
