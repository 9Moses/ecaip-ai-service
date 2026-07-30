import { TopNav } from "@/components/layout/top-nav";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <>
      <TopNav />
      <main className="flex min-h-[calc(100vh-73px)] items-center justify-center p-6">
        <Card className="w-full max-w-md" style={{ padding: "1rem" }}>
          <CardHeader>
            <CardTitle className="text-lg">
              Frontend Foundations Ready
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">
              Next.js + TypeScript + Tailwind + shadcn/ui scaffolding is
              complete.
            </p>
            <Button>Continue to Auth Setup →</Button>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
