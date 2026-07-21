"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api-client";
import { ProtectedRoute } from "@/components/protected-route";
import type { ProfileRead, ProfileUpsert, UnitPreference } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileForm />
    </ProtectedRoute>
  );
}

function ProfileForm() {
  const { fetchWithAuth } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<"idle" | "saving" | "saved">("idle");

  const [displayName, setDisplayName] = useState("");
  const [unitPreference, setUnitPreference] = useState<UnitPreference>("metric");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [heightCm, setHeightCm] = useState("");

  useEffect(() => {
    fetchWithAuth<ProfileRead>("/profile/me")
      .then((profile) => {
        setDisplayName(profile.display_name ?? "");
        setUnitPreference(profile.unit_preference);
        setDateOfBirth(profile.date_of_birth ?? "");
        setHeightCm(profile.height_cm !== null ? String(profile.height_cm) : "");
      })
      .catch((err) => {
        // No profile set up yet is expected, not an error — everything just starts blank.
        if (!(err instanceof ApiError && err.status === 404)) {
          setError("Couldn't load your profile.");
        }
      })
      .finally(() => setIsLoading(false));
  }, [fetchWithAuth]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSaveState("saving");
    const payload: ProfileUpsert = {
      display_name: displayName.trim() === "" ? null : displayName.trim(),
      unit_preference: unitPreference,
      date_of_birth: dateOfBirth === "" ? null : dateOfBirth,
      height_cm: heightCm === "" ? null : Number(heightCm),
    };
    try {
      await fetchWithAuth<ProfileRead>("/profile/me", { method: "PUT", body: payload });
      setSaveState("saved");
    } catch {
      setError("Couldn't save your profile.");
      setSaveState("idle");
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your display name, units, and body basics.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex flex-col gap-4">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              {saveState === "saved" && (
                <Alert>
                  <AlertDescription>Saved.</AlertDescription>
                </Alert>
              )}

              <div className="flex flex-col gap-2">
                <Label htmlFor="display_name">Display name</Label>
                <Input
                  id="display_name"
                  value={displayName}
                  onChange={(e) => {
                    setDisplayName(e.target.value);
                    setSaveState("idle");
                  }}
                />
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="unit_preference">Units</Label>
                <Select
                  value={unitPreference}
                  onValueChange={(value) => {
                    setUnitPreference(value as UnitPreference);
                    setSaveState("idle");
                  }}
                >
                  <SelectTrigger id="unit_preference" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="metric">Metric (kg, cm)</SelectItem>
                    <SelectItem value="imperial">Imperial (lb, in)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="date_of_birth">Date of birth</Label>
                <Input
                  id="date_of_birth"
                  type="date"
                  value={dateOfBirth}
                  onChange={(e) => {
                    setDateOfBirth(e.target.value);
                    setSaveState("idle");
                  }}
                />
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="height_cm">Height (cm)</Label>
                <Input
                  id="height_cm"
                  type="number"
                  min="0"
                  step="0.1"
                  value={heightCm}
                  onChange={(e) => {
                    setHeightCm(e.target.value);
                    setSaveState("idle");
                  }}
                />
              </div>

              <Button type="submit" disabled={saveState === "saving"}>
                {saveState === "saving" ? "Saving…" : "Save"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
