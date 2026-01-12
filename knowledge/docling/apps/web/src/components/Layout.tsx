/**
 * Zoocari Layout Component
 * Kid-friendly layout with Leesburg Animal Park branding
 */

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-leesburg-beige flex flex-col">
      {/* Header */}
      <header className="bg-leesburg-brown shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-center md:justify-start">
            <div className="text-center md:text-left">
              <h1 className="text-3xl md:text-4xl font-bold text-leesburg-yellow">
                Zoocari
              </h1>
              <p className="text-sm md:text-base text-leesburg-beige/90 mt-1">
                Ask me about the animals!
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-6 w-full max-w-4xl">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-leesburg-brown/5 border-t border-leesburg-brown/10 py-4 mt-auto">
        <div className="container mx-auto px-4 text-center">
          <p className="text-xs md:text-sm text-leesburg-brown/60">
            Powered by Leesburg Animal Park
          </p>
        </div>
      </footer>
    </div>
  );
}
