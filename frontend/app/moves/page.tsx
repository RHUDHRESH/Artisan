import Link from "next/link";

export default function MovesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center">
        <h1 className="font-serif text-4xl mb-4">No Moves Generated Yet</h1>
        <p className="text-muted-foreground max-w-md mb-8">
          Fill out your Foundation (specifically Ops -&gt; GTM Channels) to generate your first strategic moves.
        </p>
        <Link
          href="/foundation"
          className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
        >
          Go to Foundation
        </Link>
      </div>
    </div>
  );
}
