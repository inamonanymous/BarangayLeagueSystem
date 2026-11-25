export interface TableFilterState {
  search: string
  columns: Record<string, string>
}

export interface TableFilterColumn<T> {
  id: string
  label: string
  value: (row: T) => string
}

export function emptyTableFilters(): TableFilterState {
  return { search: '', columns: {} }
}

export function matchesTableFilters<T>(
  row: T,
  columns: TableFilterColumn<T>[],
  filters: TableFilterState,
): boolean {
  const normalize = (value: string) => value.trim().toLocaleLowerCase()
  const search = normalize(filters.search)
  return (!search || columns.some((column) => normalize(column.value(row)).includes(search)))
    && columns.every((column) => {
      const filter = normalize(filters.columns[column.id] ?? '')
      return !filter || normalize(column.value(row)).includes(filter)
    })
}

interface Props<T> {
  name: string
  columns: TableFilterColumn<T>[]
  filters: TableFilterState
  onChange: (filters: TableFilterState) => void
  visibleCount: number
  totalCount: number
}

function TableFilters<T>({ name, columns, filters, onChange, visibleCount, totalCount }: Props<T>) {
  const active = Boolean(filters.search.trim() || columns.some((column) => filters.columns[column.id]?.trim()))

  return <div className="table-filters" role="group" aria-label={`${name} search and filters`}>
    <div className="table-filters__bar">
      <label>Search {name}
        <input type="search" value={filters.search} onChange={(event) => onChange({ ...filters, search: event.target.value })} />
      </label>
      <button type="button" disabled={!active} onClick={() => onChange(emptyTableFilters())}>Clear filters</button>
      <span aria-live="polite">Showing {visibleCount} of {totalCount}</span>
    </div>
    <details>
      <summary>Filter columns</summary>
      <p className="muted-help">Enter text to match within a column. All filters apply together.</p>
      <div className="table-filters__columns">
        {columns.map((column) => <label key={column.id}>Filter {column.label}
          <input type="search" value={filters.columns[column.id] ?? ''} onChange={(event) => onChange({
            ...filters, columns: { ...filters.columns, [column.id]: event.target.value },
          })} />
        </label>)}
      </div>
    </details>
    {visibleCount === 0 && totalCount > 0 ? <p role="status">No rows match these filters.</p> : null}
  </div>
}

export default TableFilters
