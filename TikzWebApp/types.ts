
export interface Template {
  id: string;
  title: string;
  description: string;
  code: string;
  isOptimal?: boolean;
}

export interface Category {
  id: string;
  name: string;
  subCategories: {
    name: string;
    templates: Template[];
  }[];
}
