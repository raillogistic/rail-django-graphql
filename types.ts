// TypeScript types aligning with rail-django-graphql built-in queries

export type FilterScalar = string | number | boolean | Date | null;
export type FilterArg = FilterScalar | Array<string | number>;

export type ComplexFilterInput<FilterKey extends string = string> =
  Partial<Record<FilterKey, FilterArg>> & {
    AND?: ComplexFilterInput<FilterKey>[];
    OR?: ComplexFilterInput<FilterKey>[];
    NOT?: ComplexFilterInput<FilterKey>;
  };

export interface ModelVariables<FilterKey extends string = string> {
  filters?: ComplexFilterInput<FilterKey>;
  order_by?: string[];
  offset?: number;
  limit?: number;
  basicFilters?: Record<FilterKey, FilterArg>;
}

export interface ModelPaginatedVariables<FilterKey extends string = string> {
  filters?: ComplexFilterInput<FilterKey>;
  order_by?: string[];
  page?: number;
  per_page?: number;
  basicFilters?: Record<FilterKey, FilterArg>;
}

export interface ModelPagination {
  total_count: number;
  page_count: number;
  current_page: number;
  per_page: number;
  has_next_page: boolean;
  has_previous_page: boolean;
}

export interface ModelPaginated<T> {
  items: T[];
  page_info: ModelPagination;
}

export type ModelItems<T> = T[];

export type OrderSpec = string;

export interface TableFieldMetadata {
  name: string;
  editable: boolean;
  field_type: string;
  filterable: boolean;
  sortable: boolean;
  title: string;
  helpText: string;
  is_property: boolean;
  is_related: boolean;
}

export interface FilterOption {
  name: string;
  lookup_expr: string;
  help_text: string;
  filter_type: string;
}

export interface ModelFilterEntry {
  field_name: string;
  is_nested: boolean;
  related_model?: string | null;
  is_custom?: boolean;
  options: FilterOption[];
}

export interface ModelTableMetadata {
  app: string;
  model: string;
  verboseName: string;
  verboseNamePlural: string;
  tableName: string;
  primaryKey: string;
  ordering: string[];
  defaultOrdering: string[];
  get_latest_by: string | null;
  managers: string[];
  managed: boolean;
  fields: TableFieldMetadata[];
  filters: ModelFilterEntry[];
}