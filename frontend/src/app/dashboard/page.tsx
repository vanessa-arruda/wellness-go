"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { ProtectedRoute } from "@/components/protected-route";
import type { TodayOverview } from "@/lib/types";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <TodayDashboard />
    </ProtectedRoute>
  );
}

function TodayDashboard() {
  const { fetchWithAuth, logout } = useAuth();
  const router = useRouter();
  const [overview, setOverview] = useState<TodayOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchWithAuth<TodayOverview>("/dashboard/today")
      .then((data) => {
        if (!cancelled) setOverview(data);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load today's overview.");
      });
    return () => {
      cancelled = true;
    };
  }, [fetchWithAuth]);

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Today</h1>
        <div className="flex items-center gap-2">
          <Link href="/profile" className={buttonVariants({ variant: "ghost" })}>
            Profile
          </Link>
          <Button variant="outline" onClick={handleLogout}>
            Log out
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!overview && !error && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}

      {overview && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Workout</CardTitle>
              <CardDescription>{overview.date}</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
              {overview.scheduled.length === 0 ? (
                <p className="text-muted-foreground text-sm">Nothing scheduled for today.</p>
              ) : (
                overview.scheduled.map((entry) => (
                  <div key={entry.schedule_entry_id} className="flex items-center justify-between">
                    <span>{entry.template_name}</span>
                    <Badge variant={overview.session_completed_today ? "default" : "secondary"}>
                      {overview.session_completed_today ? "Done" : "Not started"}
                    </Badge>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Mood</CardTitle>
            </CardHeader>
            <CardContent>
              {overview.mood ? (
                <div className="flex flex-col gap-2">
                  <div className="flex flex-wrap gap-2">
                    {overview.mood.moods.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  {overview.mood.note && <p className="text-muted-foreground text-sm">{overview.mood.note}</p>}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">No check-in yet today.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Latest weight</CardTitle>
            </CardHeader>
            <CardContent>
              {overview.latest_weight ? (
                <p>
                  {overview.latest_weight.weight_kg} kg{" "}
                  <span className="text-muted-foreground text-sm">on {overview.latest_weight.recorded_at}</span>
                </p>
              ) : (
                <p className="text-muted-foreground text-sm">No weight logged yet.</p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
