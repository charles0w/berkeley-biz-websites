import data from "@/business.json";

export interface Business {
  place_id: string;
  name: string;
  tagline: string;
  about: string;
  category: string;
  address: string;
  phone: string;
  hours_raw: string[];
  rating: number;
  photos: {
    hero: string;
    gallery: string[];
  };
  google_maps_url: string;
  accent_color: string;
}

export const business = data as Business;
