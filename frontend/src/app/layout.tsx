import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Social Publisher",
  description: "Read-only dashboard of social media posts as Facebook & LinkedIn previews.",
};

const themeScript = `(function(){try{var t=localStorage.getItem('theme');if(t!=='light'&&t!=='dark'){t=window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';}if(t==='dark'){document.documentElement.classList.add('dark');}else{document.documentElement.classList.remove('dark');}}catch(e){document.documentElement.classList.add('dark');}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-gray-50 text-slate-900 dark:bg-gray-950 dark:text-gray-100">
        {children}
      </body>
    </html>
  );
}
