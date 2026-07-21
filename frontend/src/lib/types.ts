export interface ScheduledTemplateSummary {
  schedule_entry_id: string;
  template_id: string;
  template_name: string;
}

export interface MoodEntryRead {
  id: string;
  moods: string[];
  note: string | null;
  recorded_at: string;
  created_at: string;
}

export interface WeightEntryRead {
  id: string;
  weight_kg: number;
  recorded_at: string;
  created_at: string;
}

export interface TodayOverview {
  date: string;
  scheduled: ScheduledTemplateSummary[];
  session_completed_today: boolean;
  mood: MoodEntryRead | null;
  latest_weight: WeightEntryRead | null;
}

export type UnitPreference = "metric" | "imperial";

export interface ProfileRead {
  id: string;
  user_id: string;
  display_name: string | null;
  unit_preference: UnitPreference;
  date_of_birth: string | null;
  height_cm: number | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileUpsert {
  display_name: string | null;
  unit_preference: UnitPreference;
  date_of_birth: string | null;
  height_cm: number | null;
}
