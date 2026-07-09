import Image from "next/image";

export function Footer() {
  return (
    <footer className="border-t border-white/5 py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 text-center text-sm text-muted sm:flex-row sm:justify-between">
        <div className="flex items-center gap-3">
          <Image
            src="/circle_logo.png"
            alt="VehicleGrade.ca"
            width={1024}
            height={1024}
            className="h-8 w-8 rounded-full"
          />
          <p>VehicleGrade &mdash; Vehicle intelligence for smarter used car buyers.</p>
        </div>
        <p>Rule-based scoring. No machine learning. Mock data for now.</p>
      </div>
    </footer>
  );
}
