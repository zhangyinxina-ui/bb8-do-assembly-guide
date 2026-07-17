import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://zhangyinxina-ui.github.io"),
  title: "REP·LAB | BB-8 & D-O 1:1 装配指南",
  description: "BB-8 参数化 1:1 Blender 模型、D-O 资源地图与个人装配指南。",
  alternates: {
    canonical: "/bb8-do-assembly-guide/",
  },
  openGraph: {
    type: "website",
    url: "/bb8-do-assembly-guide/",
    title: "REP·LAB | BB-8 & D-O 1:1 装配指南",
    description: "1:1 Blender 模型、内部机构、工程验证、D-O 资源地图与可下载装配资料。",
    siteName: "REP·LAB",
    images: [
      {
        url: "/bb8-do-assembly-guide/og.png",
        width: 1730,
        height: 909,
        alt: "REP·LAB 1:1 robot engineering and open build log",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "REP·LAB | BB-8 & D-O 1:1 装配指南",
    description: "1:1 模型、内部机构、工程验证与可下载装配资料。",
    images: ["/bb8-do-assembly-guide/og.png"],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
