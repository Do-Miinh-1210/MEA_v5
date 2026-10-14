import type { Category } from "./types";
import React from "react";

export const SearchIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
    />
  </svg>
);

export const CopyIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"
    />
  </svg>
);

export const ChevronDownIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="m19.5 8.25-7.5 7.5-7.5-7.5"
    />
  </svg>
);

export const ChevronUpIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="m4.5 15.75 7.5-7.5 7.5 7.5"
    />
  </svg>
);

export const PaperclipIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="m18.375 12.739-7.693 7.693a4.5 4.5 0 0 1-6.364-6.364l10.94-10.94A3 3 0 1 1 19.5 7.372L8.552 18.32m.009-.01-.01.01m5.699-9.941-7.81 7.81a1.5 1.5 0 0 0 2.122 2.122l7.81-7.81"
    />
  </svg>
);

export const MicrophoneIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"
    />
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M19 10v2a7 7 0 0 1-14 0v-2"
    />
    <line x1="12" y1="19" x2="12" y2="23" />
    <line x1="8" y1="23" x2="16" y2="23" />
  </svg>
);

export const SendIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5"
    />
  </svg>
);

export const TrashIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0"
    />
  </svg>
);

export const HourglassIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M6 20.25h12m-7.5-3.493V5.625a3.375 3.375 0 0 1 6.75 0v11.132a3.375 3.375 0 0 1-6.75 0Z"
    />
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 3.75h6" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 20.25h6" />
  </svg>
);

export const BookIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"
    />
  </svg>
);

export const PencilIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
    />
  </svg>
);

export const EyeIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z"
    />
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
    />
  </svg>
);

export const ShareIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M7.217 10.907a2.25 2.25 0 1 0 0 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186 9.566-5.314m-9.566 7.5 9.566 5.314m0 0a2.25 2.25 0 1 0 3.935 2.186 2.25 2.25 0 0 0-3.935-2.186Zm0-12.814a2.25 2.25 0 1 0 3.933-2.186 2.25 2.25 0 0 0-3.933 2.186Z"
    />
  </svg>
);

export const ZapIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z"
    />
  </svg>
);

export const SaveIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    strokeWidth={1.5}
    stroke="currentColor"
    {...props}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
    />
    <polyline
      strokeLinecap="round"
      strokeLinejoin="round"
      points="17 21 17 13 7 13 7 21"
    />
    <polyline
      strokeLinecap="round"
      strokeLinejoin="round"
      points="7 3 7 8 15 8"
    />
  </svg>
);

export const LATEX_PREAMBLE_TEMPLATE = `\\documentclass[tikz,border=10mm]{standalone}
\\usepackage{tikz}
\\usepackage{amsmath}
\\usetikzlibrary{shapes.geometric,arrows.meta,calc,intersections,angles,patterns.meta,snakes,quotes,backgrounds,decorations.markings,lindenmayersystems,mindmap}
\\usepackage[utf8]{vietnam}
\\usepackage{tkz-euclide}
\\usepackage{tkz-tab}
\\usepackage{CJKutf8}
\\usepackage{tikz-3dplot,tkz-tab,tabvar}
\\usepackage{pgfplots}
\\usetikzlibrary{patterns.meta}
\\usepackage{graphicx}
\\tikzset{right angle/.style={angle}}

\\begin{document}

{CODE_PLACEHOLDER}

\\end{document}`;

export const CATEGORIES: Category[] = [
  {
    id: "math",
    name: "Toán học (SGK)",
    subCategories: [
      {
        name: "1.1. Tam giác",
        templates: [
          {
            id: "geo-tri-0",
            title: "1. Tam giác thường",
            description: "Tam giác thường",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (65:b) coordinate (A)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-1",
            title: "2. Tam giác vuông cân tại A",
            description: "Tam giác vuông cân tại A",
            code: "\\begin{tikzpicture}[declare function={r=3; k=0.5;}]\n  \\path\n  (90:r) coordinate (A)\n  (180:r) coordinate (B)\n  (0:r) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};\n  \\foreach \\x/\\y in {A/B, A/C}{\n  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n  }\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-2",
            title: "3. Tam giác tù tại A",
            description: "Tam giác tù tại A",
            code: "\\begin{tikzpicture}[declare function={r=3; }]\n  \\path\n  (110:r) coordinate (A)\n  (180:r) coordinate (B)\n  (0:r) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-3",
            title: "4. Tam giác vuông tại A",
            description: "Hai cạnh góc vuông không bằng nhau",
            code: "\\begin{tikzpicture}[declare function={a=5; c=3;}]\n  \\path\n  (0,0) coordinate (A)\n  (0:a) coordinate (B)\n  (90:c) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};\n  \\foreach \\t/\\pos in {A/225, B/-45, C/135}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-4",
            title: "5. Tam giác cân tại A",
            description: "Tam giác cân tại A",
            code: "\\begin{tikzpicture}[declare function={h=4.5; a=2.5; k=0.5;}]\n  \\path\n  (90:h) coordinate (A)\n  (180:a) coordinate (B)\n  (0:a) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\foreach \\x/\\y in {A/B, A/C}{\n  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n  }\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-5",
            title: "6. Tam giác đều",
            description: "Tam giác đều",
            code: "\\begin{tikzpicture}[declare function={r=3;}]\n  \\path\n  (90:r) coordinate (A)\n  (210:r) coordinate (B)\n  (330:r) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-6",
            title: "7. Đường trung tuyến AM",
            description: "Đường trung tuyến AM",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (50:b) coordinate (A)\n  ($(B)!k!(C)$) coordinate (M)\n  ;\n  \\draw[line width=0.6pt] (A)--(M) (A)--(B)--(C)--cycle;\n  \\foreach \\x/\\y in {B/M, M/C}{\n  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n  }\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, M/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-7",
            title: "8. Đường cao AH",
            description: "Đường cao AH",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (50:b) coordinate (A)\n  ($(B)!(A)!(C)$) coordinate (H)\n  ;\n  \\draw[line width=0.6pt] (A)--(H) (A)--(B)--(C)--cycle;\n  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=C--H--A};\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, H/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-8",
            title: "9. Đường phân giác AD",
            description: "Đường phân giác AD",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (50:b) coordinate (A)\n  ($(A)!1cm!(B)$) coordinate (Nt)\n  ($(A)!1cm!(C)$) coordinate (Mt)\n  ($(Mt)!k!(Nt)$) coordinate (Xt)\n  (intersection of A--Xt and B--C) coordinate (D)\n  ;\n  \\draw[line width=0.6pt] (A)--(D) (A)--(B)--(C)--cycle;\n  \\draw[line width=0.4pt, dashed] (Mt)--(Nt);\n  \\path\n  pic[draw, line width=0.6pt, angle radius=7pt]{angle=B--A--D}\n  pic[draw, line width=0.6pt, angle radius=9pt]{angle=D--A--C}\n  ;\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, D/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-9",
            title: "10. Đường trung bình MN",
            description: "Đường trung bình MN",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (50:b) coordinate (A)\n  ($(A)!k!(B)$) coordinate (M)\n  ($(A)!k!(C)$) coordinate (N)\n  ;\n  \\draw[line width=0.6pt] (M)--(N) (A)--(B)--(C)--cycle;\n  \\foreach \\x/\\y in {A/M, M/B}{\n  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n  }\n  \\foreach \\x/\\y in {A/N, N/C}{\n  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\n  \\tikz{\n  \\draw[line width=0.6pt, shift={(-1pt,0)}] (-90:1.5pt)--(90:1.5pt);\n  \\draw[line width=0.6pt, shift={(1pt,0)}] (-90:1.5pt)--(90:1.5pt);\n  }\n  };\n  }\n  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, M/180, N/0}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-10",
            title: "11. Trọng tâm G",
            description: "Trọng tâm G",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (70:b) coordinate (A)\n  ($(A)!k!(B)$) coordinate (D)\n  ($(B)!k!(C)$) coordinate (E)\n  ($(C)!k!(A)$) coordinate (F)\n  (intersection of A--E and B--F) coordinate (G)\n  ;\n  \\draw[line width=0.6pt] (A)--(E) (B)--(F) (C)--(D) (A)--(B)--(C)--cycle;\n  \\draw[line width=0.4pt, dashed] (C)--(D);\n  \\foreach \\x/\\y in {A/D, D/B}{\n  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n  }\n  \\foreach \\x/\\y in {B/E, E/C}{\n  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n  }\n  \\foreach \\x/\\y in {C/F, F/A}{\n  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\n  \\tikz{\n  \\draw[line width=0.6pt, shift={(-1pt,0)}] (-90:1.5pt)--(90:1.5pt);\n  \\draw[line width=0.6pt, shift={(1pt,0)}] (-90:1.5pt)--(90:1.5pt);\n  }\n  };\n  }\n  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, G/60, D/150, E/-90, F/60}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-11",
            title: "12. Trực tâm H",
            description: "Trực tâm H",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (65:b) coordinate (A)\n  ($(A)!(C)!(B)$) coordinate (D)\n  ($(B)!(A)!(C)$) coordinate (E)\n  ($(C)!(B)!(A)$) coordinate (F)\n  (intersection of A--E and B--F) coordinate (H)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\draw[line width=0.4pt, dashed] (A)--(E) (B)--(F) (C)--(D);\n  \\foreach \\x/\\y/\\z in {C/E/A, B/F/C, B/D/C}{\n  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=\\x--\\y--\\z};\n  }\n  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, H/5, D/150, E/-90, F/60}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-12",
            title: "13. Đường tròn ngoại tiếp",
            description: "(tâm O)",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (70:b) coordinate (A)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\begin{scope}[overlay]\n  \\path\n  ($(A)!k!(B)$) coordinate (Nt)\n  ($(Nt)!1!90:(A)$) coordinate (Xt)\n  ($(B)!k!(C)$) coordinate (Mt)\n  ($(Mt)!1!90:(B)$) coordinate (Yt)\n  (intersection of Nt--Xt and Mt--Yt) coordinate (O)\n  ;\n  \\end{scope}\n  \\draw[line width=0.4pt, dashed] (Nt)--(Xt) (Mt)--(Yt);\n  \\draw[line width=0.6pt] let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)});\n  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, O/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-tri-13",
            title: "14. Đường tròn nội tiếp",
            description: "(tâm I)",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5; t=0.5; m=1cm;}]\n  \\path\n  (0,0) coordinate (B)\n  (0:a) coordinate (C)\n  (70:b) coordinate (A)\n  ($(A)!m!(B)$) coordinate (Nt)\n  ($(A)!m!(C)$) coordinate (Mt)\n  ($(Mt)!k!(Nt)$) coordinate (Xt)\n  ($(B)!m!(C)$) coordinate (Kt)\n  ($(B)!m!(A)$) coordinate (Lt)\n  ($(Kt)!t!(Lt)$) coordinate (Yt)\n  (intersection of A--Xt and B--Yt) coordinate (I)\n  ($(A)!(I)!(B)$) coordinate (D)\n  ($(B)!(I)!(C)$) coordinate (E)\n  ($(C)!(I)!(A)$) coordinate (F)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n  \\draw[line width=0.4pt, dashed] (A)--(Xt) (B)--(Yt);\n  \\draw[line width=0.6pt] let \\p1=($(I)-(D)$) in (I) circle ({veclen(\\x1,\\y1)});\n  \\draw[line width=0.4pt, dashed] (I)--(D);\n  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, I/-60, D/150, E/-90, F/60}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};\n  }\n\\end{tikzpicture}",
          },
        ],
      },
      {
        name: "1.2. Đa giác",
        templates: [
          {
            id: "geo-poly-0",
            title: "1. Tứ giác lồi nội tiếp (bất kỳ)",
            description: "Tứ giác lồi nội tiếp đường tròn",
            code: "\\begin{tikzpicture}[declare function={r=3;}]\n  \\path\n  (120:r) coordinate (A)\n  (45:r) coordinate (B)\n  (-30:r) coordinate (C)\n  (210:r) coordinate (D)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-1",
            title: "2. Hình bình hành (tổng quát)",
            description: "Hình bình hành",
            code: "\\begin{tikzpicture}[declare function={a=3; b=5; h=3.5; k=0.5;}]\n  \\path\n  (0,0) coordinate (A)\n  (0:a) coordinate (B)\n  (-110:h) coordinate (D)\n  ($(D)+(B)-(A)$) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-2",
            title: "3. Hình thang cân",
            description: "Hình thang cân",
            code: "\\begin{tikzpicture}[declare function={a=3; h=3.5; goc=-130; k=0.5;}]\n  \\path\n  (0,0) coordinate (A)\n  (0:a) coordinate (B)\n  (goc:h) coordinate (D)\n  ($(B)+({-180-goc}:h)$) coordinate (C)\n  ;\n  \\foreach \\x/\\y in {A/D, B/C}{\n  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n  }\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-3",
            title: "4. Hình thang vuông",
            description: "Hình thang vuông",
            code: "\\begin{tikzpicture}[declare function={a=3.5; h=3; goc=-60; c=abs(h/sin(goc)); k=1;}]\n  \\path\n  (0,0) coordinate (A)\n  (0:a) coordinate (B)\n  (-90:h) coordinate (D)\n  ($(B)+(goc:c)$) coordinate (C)\n  ;\n  \\foreach \\x/\\y/\\z in {D/A/B, C/D/A}{\n  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=\\x--\\y--\\z};\n  }\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-4",
            title: "5. Hình bình hành (cách dựng phân tích)",
            description: "Hình bình hành",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3;}]\n  \\path\n  (0,0) coordinate (A)\n  (0:a) coordinate (B)\n  (-120:b) coordinate (D)\n  ($(D)+(B)-(A)$) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-5",
            title: "6. Hình chữ nhật",
            description: "Hình chữ nhật",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3;}]\n  \\path\n  (0,0) coordinate (A)\n  (0:a) coordinate (B)\n  (-90:b) coordinate (D)\n  ($(D)+(B)-(A)$) coordinate (C)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-6",
            title: "7. Hình vuông (có tâm O)",
            description: "Hình vuông",
            code: "\\begin{tikzpicture}[declare function={a=5; k=0.5;}]\n  \\path\n  (0,0) coordinate (A)\n  (0:a) coordinate (B)\n  (-90:a) coordinate (D)\n  ($(D)+(B)-(A)$) coordinate (C)\n  ($(A)!k!(C)$) coordinate (O)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/135, B/45, C/-45, D/225}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-7",
            title: "8. Hình thoi",
            description: "Hình thoi",
            code: "\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]\n  \\path\n  (90:{0.5*b}) coordinate (A)\n  (0:{0.5*a}) coordinate (B)\n  (270:{0.5*b}) coordinate (C)\n  (180:{0.5*a}) coordinate (D)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;\n  \\foreach \\t/\\g in {A/90, B/0, C/-90, D/180}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-8",
            title: "9. Ngũ giác đều",
            description: "Ngũ giác đều",
            code: "\\begin{tikzpicture}[declare function={r=3; goc=360/5;}]\n  \\path\n  (90:r) coordinate (A)\n  ({90+goc}:r) coordinate (B)\n  ({90+2*goc}:r) coordinate (C)\n  ({90+3*goc}:r) coordinate (D)\n  ({90+4*goc}:r) coordinate (E)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--(E)--cycle;\n  \\foreach[count=\\i] \\t in {A,B,C,D,E}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={({90-goc+goc*\\i}:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-9",
            title: "10. Lục giác đều",
            description: "Lục giác đều",
            code: "\\begin{tikzpicture}[declare function={r=3; goc=60;}]\n  \\path\n  (90:r) coordinate (A)\n  ({90+goc}:r) coordinate (B)\n  ({90+2*goc}:r) coordinate (C)\n  ({90+3*goc}:r) coordinate (D)\n  ({90+4*goc}:r) coordinate (E)\n  ({90+5*goc}:r) coordinate (F)\n  ;\n  \\draw[line width=0.6pt] (A)--(B)--(C)--(D)--(E)--(F)--cycle;\n  \\foreach[count=\\i] \\t in {A,B,C,D,E,F}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={({90-goc+goc*\\i}:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-poly-10",
            title: "11. Ngôi sao 5 cánh",
            description: "Ngôi sao 5 cánh",
            code: "\\begin{tikzpicture}[declare function={r=3; goc=360/5;}]\n  \\path\n  (90:r) coordinate (A)\n  ({90+goc}:r) coordinate (B)\n  ({90+2*goc}:r) coordinate (C)\n  ({90+3*goc}:r) coordinate (D)\n  ({90+4*goc}:r) coordinate (E)\n  ;\n  \\draw[line width=0.6pt] (A)--(C)--(E)--(B)--(D)--cycle;\n  \\foreach[count=\\i] \\t in {A,B,C,D,E}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={({90-goc+goc*\\i}:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
        ],
      },
      {
        name: "1.3. Đường tròn",
        templates: [
          {
            id: "geo-circ-0",
            title: "1. Đường tròn tâm O",
            description: "Đường tròn và điểm A",
            code: "\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (45:r) coordinate (A)\n  ;\n  \\draw (O)--(A) node[above, pos=0.5, sloped, font=\\normalsize]{$r$};\n  \\draw let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)});\n  \\foreach \\t/\\g in {A/45, O/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-1",
            title: "2. Đường tròn đường kính AB",
            description: "Tròn đường kính",
            code: "\\begin{tikzpicture}[declare function={r=3; k=0.5;}, line width=0.6pt]\n  \\path\n  (180:r) coordinate (A)\n  (0:r) coordinate (B)\n  ($(A)!k!(B)$) coordinate (O)\n  ;\n  \\draw (B)--(A);\n  \\draw let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)});\n  \\foreach \\t/\\g in {A/180, B/0, O/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-2",
            title: "3. Tiếp tuyến tại A",
            description: "Tiếp tuyến tại 1 điểm",
            code: "\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (-45:r) coordinate (A)\n  ($(A)!1!-90:(O)$) coordinate (T)\n  ($2*(A)-(T)$) coordinate (Th)\n  ;\n  \\path pic[draw, angle radius=5pt]{right angle=O--A--T};\n  \\draw\n  (O)--(A)\n  (T)--(Th)\n  let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)})\n  ;\n  \\foreach \\t/\\g in {A/-90, O/90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-3",
            title: "4. Tứ giác đối xứng nội tiếp",
            description: "Hình thoi nội tiếp",
            code: "\\begin{tikzpicture}[declare function={r=3; goc=55; k=1;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (goc:r) coordinate (A)\n  (-goc:r) coordinate (B)\n  ;\n  \\begin{scope}[overlay]\n  \\path\n  ($(A)!k!-90:(O)$) coordinate (OA)\n  ($(B)!k!-90:(O)$) coordinate (OB)\n  (intersection of A--OA and B--OB) coordinate (S)\n  ;\n  \\end{scope}\n  \\path\n  pic[draw, angle radius=5pt]{right angle=O--A--S}\n  pic[draw, angle radius=5pt]{right angle=O--B--S}\n  ;\n  \\draw\n  (O)--(A)--(S)--(B)--cycle\n  let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)})\n  ;\n  \\foreach \\t/\\g in {A/goc, B/-goc, S/0, O/135}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-4",
            title: "5. Nửa đường tròn",
            description: "Nửa đường tròn",
            code: "\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (180:r) coordinate (A)\n  (0:r) coordinate (B)\n  ;\n  \\draw (B) arc (0:180:r)--cycle;\n  \\foreach \\t/\\g in {A/180, B/0, O/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-5",
            title: "6. Hình thang cân nội tiếp",
            description: "Nội tiếp nửa đường tròn",
            code: "\\begin{tikzpicture}[declare function={r=3; k=1;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (180:r) coordinate (A)\n  (0:r) coordinate (B)\n  (65:r) coordinate (C)\n  ;\n  \\begin{scope}[overlay]\n  \\path\n  ($(A)!k!-90:(O)$) coordinate (OA)\n  ($(B)!k!-90:(O)$) coordinate (OB)\n  ($(C)!k!-90:(O)$) coordinate (OC)\n  (intersection of A--OA and C--OC) coordinate (M)\n  (intersection of B--OB and C--OC) coordinate (N)\n  ;\n  \\end{scope}\n  \\draw\n  (A)--(M)--(N)--(B)--cycle\n  (B) arc (0:180:r)\n  ;\n  \\foreach \\t/\\g in {A/180, B/0, O/-90, M/180, N/0, C/65}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-6",
            title: "7. Tứ giác nội tiếp đường tròn",
            description: "Tứ giác nội tiếp",
            code: "\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (120:r) coordinate (A)\n  (45:r) coordinate (B)\n  (-30:r) coordinate (C)\n  (210:r) coordinate (D)\n  ;\n  \\draw\n  (A)--(B)--(C)--(D)--cycle\n  (O) circle (r)\n  ;\n  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210, O/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-7",
            title: "8. Tứ giác ngoại tiếp đường tròn",
            description: "Ngoại tiếp",
            code: "\\begin{tikzpicture}[declare function={r=2.5; k=1;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (-90:r) coordinate (M)\n  (75:r) coordinate (N)\n  (25:r) coordinate (P)\n  (155:r) coordinate (Q)\n  ;\n  \\begin{scope}[overlay]\n  \\path\n  ($(M)!k!-90:(O)$) coordinate (AB)\n  ($(N)!k!-90:(O)$) coordinate (CD)\n  ($(P)!k!-90:(O)$) coordinate (BC)\n  ($(Q)!k!-90:(O)$) coordinate (AD)\n  (intersection of AB--M and Q--AD) coordinate (A)\n  (intersection of AB--M and P--BC) coordinate (B)\n  (intersection of CD--N and Q--AD) coordinate (D)\n  (intersection of CD--N and P--BC) coordinate (C)\n  ;\n  \\end{scope}\n  \\draw\n  (A)--(B)--(C)--(D)--cycle\n  (O) circle (r)\n  ;\n  \\foreach \\t/\\g in {A/-90, B/-90, C/0, D/180, O/-90}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-8",
            title: "9. Tiếp tuyến kẻ từ S",
            description: "Một tiếp tuyến",
            code: "\\begin{tikzpicture}[declare function={r=3; gocm=50; goch=-35;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (gocm:r) coordinate (A)\n  ({180-goch}:r) coordinate (B)\n  (goch:r) coordinate (C)\n  ;\n  \\begin{scope}[overlay]\n  \\path\n  ($(A)!1!-90:(O)$) coordinate (OA)\n  (intersection of A--OA and B--C) coordinate (S)\n  ;\n  \\end{scope}\n  \\path pic[draw, angle radius=5pt]{right angle=O--A--S};\n  \\draw\n  (O)--(A)--(S)--(B)\n  let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)})\n  ;\n  \\foreach \\t/\\g in {A/gocm, B/{180-goch}, C/goch, S/0, O/135}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-9",
            title: "10. Hai đường tròn tiếp xúc ngoài",
            description: "Tiếp xúc",
            code: "\\begin{tikzpicture}[\n  declare function={\n    R=3;\n    r=0.35*R;\n    d=R+r+2;\n    goc=acos((R-r)/d);\n    goch=acos((R+r)/d);\n    k=1;\n  },\n  line width=0.6pt\n]\n  \\path\n  (0,0) coordinate (O)\n  (d,0) coordinate (O')\n  (goc:R) coordinate (A)\n  (-goc:R) coordinate (B)\n  (goch:R) coordinate (C)\n  (-goch:R) coordinate (D)\n  ($(d,0)+(goc:r)$) coordinate (A')\n  ($(d,0)+(-goc:r)$) coordinate (B')\n  (intersection of A--A' and B--B') coordinate (S)\n  ;\n  \\foreach \\x/\\y/\\z in {O/A/S, O/B/S}{\n  \\path pic[draw, angle radius=5pt]{right angle=\\x--\\y--\\z};\n  }\n  \\draw\n  (O) circle (R)\n  (O') circle (r)\n  (A)--(S)--(B)--(O)--cycle\n  ;\n  \\foreach \\t/\\g in {A/goc, A'/goc, B/-goc, B'/-goc, O/180, O'/-90, S/0}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-10",
            title: "11. Hai đường tròn cắt nhau",
            description: "Cắt nhau",
            code: "\\begin{tikzpicture}[\n  declare function={\n    R=3;\n    r=1.5;\n    d=R+r;\n    goc=acos((R-r)/d);\n    goch=acos((R+r)/d);\n  },\n  line width=0.6pt\n]\n  \\path\n  (0,0) coordinate (O)\n  (0:d) coordinate (O')\n  (goc:R) coordinate (A)\n  (-goc:R) coordinate (B)\n  (goch:R) coordinate (C)\n  (-goch:R) coordinate (D)\n  ($(0:d)+(goc:r)$) coordinate (A')\n  ($(0:d)+(-goc:r)$) coordinate (B')\n  (intersection of A--A' and B--B') coordinate (S)\n  ;\n  \\draw\n  (O) circle (R)\n  (O') circle (r)\n  (A)--(S)--(B)\n  ;\n  \\foreach \\t/\\g in {A/goc, A'/goc, B/-goc, B'/-goc, O/-90, O'/-90, S/0}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-circ-11",
            title: "12. Hai đường tròn tiếp xúc trong",
            description: "Tiếp xúc",
            code: "\\begin{tikzpicture}[declare function={R=5; r=2; d=R-r;}, line width=0.6pt]\n  \\path\n  (0,0) coordinate (O)\n  (0:d) coordinate (O')\n  (0:R) coordinate (A)\n  ;\n  \\draw\n  (O) circle (R)\n  (O') circle (r)\n  ;\n  \\foreach \\t/\\g in {O/180, O'/-90, A/0}{\n  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};\n  }\n\\end{tikzpicture}",
          },
        ],
      },
      {
        name: "1.4. Đường cônic",
        templates: [
          {
            id: "geo-conic-0",
            title: "1. Đường Elip",
            description: "Đường elip",
            code: "\\begin{tikzpicture}[declare function={a=2.5; b=2;}]\n  \\draw[line width=0.6pt] (0,0) ellipse (a and b);\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-1",
            title: "2. Parabol hướng lên",
            description: "Parabol y = a*x^2",
            code: "\\begin{tikzpicture}[declare function={a=0.65; xmin=-4; xmax=4; ymin=-1; ymax=5.15;}]\n  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};\n  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[below left] {$y$};\n  \\begin{scope}\n  \\clip (xmin, ymin) rectangle (xmax, ymax);\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-3:3] plot (\\x, {a*(\\x)^2});\n  \\end{scope}\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-2",
            title: "3. Parabol hướng sang phải",
            description: "Parabol x = a*y^2",
            code: "\\begin{tikzpicture}[declare function={a=0.65; xmin=-1; xmax=4; ymin=-3.25; ymax=3.25;}]\n  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};\n  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};\n  \\begin{scope}\n  \\clip (xmin, ymin) rectangle (xmax, ymax);\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-3.5:3.5] plot ({a*(\\x)^2}, \\x);\n  \\end{scope}\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-3",
            title: "4. Elip với tiêu điểm",
            description: "Elip và bán kính vectơ",
            code: "\\begin{tikzpicture}[\n  declare function={\n    a=2.5;\n    b=2;\n    xmin=-a-0.5;\n    xmax=-xmin;\n    ymin=-b-0.5;\n    ymax=-ymin;\n    c=sqrt(a^2-b^2);\n  }\n]\n  \\path\n  (60:a and b) coordinate (M)\n  (0:c) coordinate (F2)\n  (180:c) coordinate (F1)\n  ;\n  \\draw[dashed, line width=0.6pt] (F1) -- (M) -- (F2);\n  \\draw[line width=0.6pt] (0,0) ellipse (a and b);\n  \\foreach \\p/\\pos/\\lab in {M/115/M, F2/-90/F_2, F1/-90/F_1} {\n  \\draw[line width=0.6pt] (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-4",
            title: "5. Hyperbol với tiếp tuyến",
            description: "Hyperbol",
            code: "\\begin{tikzpicture}[\n  declare function={\n    a=0.65;\n    b=0.6;\n    c=sqrt(a^2+b^2);\n    goc=0.75;\n  }\n]\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({a*cosh(\\x)}, {b*sinh(\\x)});\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({-a*cosh(\\x)}, {b*sinh(\\x)});\n  \\path\n  let \\n1={4*c} in\n  (180:c) coordinate (F1)\n  (0:c) coordinate (F2)\n  ({a*cosh(goc)}, {b*sinh(goc)}) coordinate (M)\n  ($(F1)!\\n1 cm!(M)$) coordinate (A)\n  ;\n  \\draw[cyan, line width=0.6pt] (F2) -- (M) -- (A);\n  \\foreach \\p/\\pos/\\lab in {F1/180/F_1, F2/0/F_2, M/135/M, A/0/A} {\n  \\draw[line width=0.6pt] (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-5",
            title: "6. Elip đầy đủ",
            description: "Đầy đủ các điểm đặc biệt",
            code: "\\begin{tikzpicture}[\n  declare function={\n    a=2.5;\n    b=2;\n    xmin=-a-0.5;\n    xmax=-xmin;\n    ymin=-b-0.5;\n    ymax=-ymin;\n    goc=60;\n    c=sqrt(a^2-b^2);\n  }\n]\n  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};\n  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};\n  \\path\n  (0,0) coordinate (O)\n  (goc:a and b) coordinate (M)\n  (180:a) coordinate (A')\n  (0:a) coordinate (A2)\n  (-90:b) coordinate (B')\n  (90:b) coordinate (B2)\n  (0:c) coordinate (F2)\n  (180:c) coordinate (F1)\n  ;\n  \\draw[dashed, line width=0.6pt] (F1) -- (M) -- (F2);\n  \\draw[line width=0.6pt] (0,0) ellipse (a and b);\n  \\foreach \\p/\\pos/\\lab in {\n  O/-135/O,\n  A1/-135/A_1,\n  A2/-45/A_2,\n  B1/-45/B_1,\n  B2/45/B_2,\n  F1/-90/F_1,\n  F2/-90/F_2,\n  M/45/M\n  } {\n  \\draw[line width=0.6pt] (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-6",
            title: "7. Hyperbol đầy đủ",
            description: "Đầy đủ với tiệm cận",
            code: "\\begin{tikzpicture}[\n  declare function={\n    a=1.5;\n    b=1.3;\n    c=sqrt(a^2+b^2);\n    goc=0.75;\n    xmin=-4;\n    xmax=4.25;\n    ymin=-2.5;\n    ymax=2.75;\n  }\n]\n  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};\n  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};\n  \\begin{scope}\n  \\clip (xmin, ymin) rectangle (xmax, ymax);\n  \\draw[dashed, line width=0.6pt, smooth, samples=30, domain=-8:8] plot (\\x, {-(b/a)*\\x});\n  \\draw[dashed, line width=0.6pt, smooth, samples=30, domain=-8:8] plot (\\x, {(b/a)*\\x});\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({a*cosh(\\x)}, {b*sinh(\\x)});\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({-a*cosh(\\x)}, {b*sinh(\\x)});\n  \\end{scope}\n  \\draw[dashed, line width=0.6pt] (-a,-b) rectangle (a,b);\n  \\path\n  (a,b) coordinate (P)\n  (90:b) coordinate (B2)\n  (-a,b) coordinate (Q)\n  (180:a) coordinate (A')\n  (0,0) coordinate (O)\n  (-a,-b) coordinate (R)\n  (-90:b) coordinate (B')\n  (a,-b) coordinate (S)\n  (0:a) coordinate (A2)\n  (180:c) coordinate (F1)\n  (0:c) coordinate (F2)\n  ;\n  \\foreach \\p/\\pos/\\lab in {\n  P/120/P,\n  B2/45/B_2,\n  Q/60/Q,\n  A1/-45/A_1,\n  O/-135/O,\n  R/-60/R,\n  B1/-45/B_1,\n  S/240/S,\n  A2/-45/A_2,\n  F1/-90/F_1,\n  F2/-90/F_2\n  } {\n  \\draw[line width=0.6pt] (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-7",
            title: "8. Parabol đầy đủ",
            description: "Với tiêu điểm và đường chuẩn",
            code: "\\begin{tikzpicture}[\n  declare function={\n    p=0.45;\n    xt=1.5;\n    xmin=-3.25;\n    xmax=3.25;\n    ymin=-1.5*p;\n    ymax=4;\n  }\n]\n  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};\n  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};\n  \\begin{scope}[color=teal!85!blue]\n  \\clip (-3.5, {-1.5*p}) rectangle (3.5, 4.1);\n  \\path\n  (0, {-0.5*p}) coordinate (A)\n  (xt, {-0.5*p}) coordinate (B)\n  (xt, {2*p*xt*xt}) coordinate (M)\n  (0, {0.5*p}) coordinate (F)\n  ;\n  \\path pic[draw, angle radius=5pt, line width=0.6pt]{right angle=A--B--M};\n  \\draw[dashed, line width=0.6pt] (B) -- (M) -- (F);\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-3.5:3.5] plot (\\x, {2*p*(\\x)^2});\n  \\draw[line width=0.6pt] (-3, {-0.5*p}) -- (3, {-0.5*p}) node[shift={(0.25,-0.25)}, font=\\normalsize] {$\\Delta$};\n  \\foreach \\p/\\pos/\\lab in {F/150/F, M/10/M, B/-90/A} {\n  \\draw[line width=0.6pt] (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};\n  }\n  \\end{scope}\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-8",
            title: "9. Tiếp tuyến elip tại 1 điểm",
            description: "Elip với tiếp tuyến",
            code: "\\begin{tikzpicture}[\n  declare function={\n    a=2.5;\n    b=0.65*a;\n    goc=60;\n    xv=a*sin(goc);\n    yv=-b*cos(goc);\n  }\n]\n  \\path\n  (goc:a and b) coordinate (M)\n  ($(M)+(xv,yv)$) coordinate (A')\n  ($(M)!3cm!(A')$) coordinate (T1)\n  ($2*(M)-(T1)$) coordinate (T2)\n  ;\n  \\draw[line width=0.6pt] (T1) -- (T2);\n  \\draw[line width=0.6pt] (0,0) ellipse (a and b);\n  \\draw[line width=0.6pt] (M) circle (0.8pt) node[shift={(goc:8pt)}, font=\\normalsize] {$M$};\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-9",
            title: "10. Tiếp tuyến hyperbol tại 2 điểm",
            description: "Hyperbol",
            code: "\\begin{tikzpicture}[\n  declare function={\n    a=0.65;\n    b=0.6;\n    c=sqrt(a^2+b^2);\n    goc=1.25;\n  }\n]\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({a*cosh(\\x)}, {b*sinh(\\x)});\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({-a*cosh(\\x)}, {b*sinh(\\x)});\n  \\path\n  (180:c) coordinate (F1)\n  (0:c) coordinate (F2)\n  ({a*cosh(goc)}, {b*sinh(goc)}) coordinate (M)\n  ({a*sinh(goc)}, {b*cosh(goc)}) coordinate (Mt)\n  ($(M)+(Mt)$) coordinate (A')\n  ($(M)!2cm!(A')$) coordinate (T1)\n  ($2*(M)-(T1)$) coordinate (T2)\n  ;\n  \\path\n  ({-a*cosh(goc)}, {b*sinh(goc)}) coordinate (N)\n  ({a*sinh(goc)}, {-b*cosh(goc)}) coordinate (Nt)\n  ($(N)+(Nt)$) coordinate (B')\n  ($(N)!2cm!(B')$) coordinate (K1)\n  ($2*(N)-(K1)$) coordinate (K2)\n  ;\n  \\draw[blue, line width=0.6pt] (T1) -- (T2);\n  \\draw[blue, line width=0.6pt] (K1) -- (K2);\n  \\foreach \\p/\\pos/\\lab in {M/135/M, N/45/N} {\n  \\draw[line width=0.6pt] (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};\n  }\n\\end{tikzpicture}",
          },
          {
            id: "geo-conic-10",
            title: "11. Parabol với tiếp tuyến",
            description: "Tiếp tuyến parabol",
            code: "\\begin{tikzpicture}[\n  declare function={\n    a=0.65;\n    xt=1;\n    xmin=-1;\n    xmax=4;\n    ymin=-3;\n    ymax=3;\n  }\n]\n  \\path\n  ({a*(xt)*(xt)}, xt) coordinate (M)\n  ({2*a*xt}, 1) coordinate (vt)\n  ($(M)+(vt)$) coordinate (Xt)\n  ($(M)!2cm!(Xt)$) coordinate (X) \n  ($2*(M)-(X)$) coordinate (Y)\n  ;\n  \\draw[line width=0.6pt, smooth, samples=150, domain=-2.5:2.5] plot ({a*(\\x)^2}, \\x);\n  \\draw[line width=0.6pt] (M) -- (X) node[pos=1, shift={(-0.5,0.1)}, font=\\normalsize] {$(t_M)$} -- (Y);\n  \\draw[line width=0.6pt] (M) circle (0.8pt) node[shift={(120:8pt)}, font=\\normalsize] {$M$};\n\\end{tikzpicture}",
          },
        ],
      },
      {
        name: "1.5. Đa diện",
        templates: [
          {
            id: "dyn_item_fiyyoq_0",
            title: "1. Hình chóp tứ giác",
            description: "đáy hình thang",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=4;}]\n \\path\n (0,0) coordinate (B)\n (0:a) coordinate (C)\n (-45:b) coordinate (D)\n (\$(D)+(0,h)\$) coordinate (A)\n ;\n \\draw[dashed, line width=0.4pt] (B)--(C);\n \\draw[line width=0.6pt]\n (A)--(D)\n (A)--(B)--(D)--(C)--cycle\n ;\n \\foreach \\x/\\goc in {A/90, B/240, C/-60, D/-90}{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\x\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_vjp36g_1",
            title: "2. Hình chóp tam giác vuông",
            description: "đáy là tam giác vuông",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=4;}]\n \\path\n (0,0) coordinate (A)\n (0:a) coordinate (C)\n (-45:b) coordinate (B)\n (\$(A)+(90:h)\$) coordinate (S)\n ;\n \\foreach \\x/\\y/\\z in {B/A/S, C/A/S}{\n \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=\\x--\\y--\\z};\n }\n \\draw[dashed, line width=0.4pt] (A)--(C);\n \\draw[line width=0.6pt]\n (S)--(B)\n (S)--(A)--(B)--(C)--cycle\n ;\n \\foreach \\x/\\goc in {S/90, A/190, B/-90, C/0}{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\x\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_hnqvfg_2",
            title: "3. Tam giác vuông",
            description: "hình phẳng",
            code: `\\begin{tikzpicture}[declare function={a=5; c=3;}]\n \\path\n (0,0) coordinate (A)\n (0:a) coordinate (B)\n (90:c) coordinate (C)\n ;\n \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};\n \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;\n \\foreach \\t/\\g in {A/225, B/-45, C/135}{\n \\draw (\\t) circle (0.6pt) node[shift={(\\goc:8pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_k7sbns_3",
            title: "4. Hình chóp có đáy hình thang",
            description: "dạng elip",
            code: `\\begin{tikzpicture}[declare function={r=2.5;}]\n \\path\n (90:{r*1.25}) coordinate (A)\n (160:{r} and {r*0.35}) coordinate (B)\n (20:{r} and {r*0.35}) coordinate (C)\n (260:{r} and {r*0.5}) coordinate (D)\n ;\n \\draw[dashed, line width=0.4pt] (B)--(C);\n \\draw[line width=0.6pt]\n (A)--(D)\n (A)--(B)--(D)--(C)--cycle\n ;\n \\foreach \\x/\\goc in {A/90, B/180, C/0, D/-90}{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\x\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_l5fagt_4",
            title: "5. Hình chóp cụt",
            description: "đáy dưới là hình bình hành",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=3.5; k=0.5;}]\n \\path\n (0,0) coordinate (A)\n (0:a) coordinate (D)\n (-135:b) coordinate (B)\n (\$(B)+(D)-(A)\$) coordinate (C)\n (\$(A)+ (90:h)\$) coordinate (S)\n ;\n \\draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);\n \\draw[line width=0.6pt]\n (S)--(B)--(C)--(D)--cycle\n (S)--(C)\n ;\n \\foreach \\t/\\g in {A/170, B/-90, C/-90, D/0, S/90}{\n \\draw (\\t) circle (0.6pt) node[shift={(\\goc:8pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_z2lfz_5",
            title: "6. Hình chóp cụt 2",
            description: "có dấu bằng trên các cạnh",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=4; k=0.5;}]\n \\path\n (0,0) coordinate (A)\n (0:a) coordinate (D)\n (-135:b) coordinate (B)\n (\$(B)+(D)-(A)\$) coordinate (C)\n (\$(0,h)+(-135:{0.35*b})\$) coordinate (S)\n ;\n \\foreach \\x/\\y in {S/A, S/B}{\n \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};\n }\n \\draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);\n \\draw[line width=0.6pt]\n (S)--(B)--(C)--(D)--cycle\n (S)--(C)\n ;\n \\foreach \\t/\\g in {A/170, B/-90, C/-90, D/0, S/90}{\n \\draw (\\t) circle (0.6pt) node[shift={(\\goc:8pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_l9wmjx_6",
            title: "7. Hình lăng trụ đứng",
            description: "đáy là hình thang",
            code: `\\begin{tikzpicture}[declare function={a=4; b=0.5*a; h=1.25*a; k=0.5;}]\n \\path\n (0:0) coordinate (A)\n (220:b) coordinate (B)\n (0:a) coordinate (D)\n (\$(B)+(D)-(A)\$) coordinate (C)\n ;\n \\foreach \\x in {A,B,C,D}{\n \\path (\\x)++(90:h) coordinate (\\x');\n }\n \\draw[dashed, line width=0.4pt] (A')--(A)--(B) (A)--(D);\n \\draw[line width=0.6pt]\n (B')--(A')--(D')--(C')\n (D')--(D)--(C)\n (B)--(C)--(C')--(B')--cycle\n ;\n \\foreach \\x/\\goc/\\t in {\n A/45/A, B/-90/B, C/-90/C, D/0/D,\n A1/90/A', B1/90/B', C1/90/C', D1/90/D'\n }{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_4onilw_7",
            title: "8. Hình chóp có đáy hình bình hành",
            description: "các góc vuông tại A",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=3.5; k=0.5;}]\n \\path\n (0,0) coordinate (A)\n (0:a) coordinate (D)\n (-135:b) coordinate (B)\n (\$(B)+(D)-(A)\$) coordinate (C)\n (0,h) coordinate (S)\n ;\n \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--S};\n \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=D--A--S};\n \\draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);\n \\draw[line width=0.6pt]\n (S)--(B)--(C)--(D)--cycle\n (S)--(C)\n ;\n \\draw (A) circle (0.6pt) node[shift={(170:12pt)}, font=\\normalsize]{\$A\$};\n \\foreach \\t/\\g in { B/-90, C/-90, D/0, S/90}{\n \\draw (\\t) circle (0.6pt) node[shift={(\\goc:8pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_juehqi_8",
            title: "9. Hình lăng trụ tam giác",
            description: "lăng trụ tam giác",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=4.5; k=0.5;}]\n \\path\n (0:0) coordinate (A)\n (-43:b) coordinate (B)\n (0:a) coordinate (C)\n ;\n \\foreach \\x in {A,B,C}{\n \\path (\\x)++(90:h) coordinate (\\x1);\n }\n \\draw[dashed, line width=0.4pt] (A)--(C);\n \\draw[line width=0.6pt]\n (B')--(A')--(C')--cycle\n (A')--(A)--(B)--(B')\n (C')--(C)--(B)\n ;\n \\foreach \\x/\\goc/\\t in {\n A/180/A, B/-90/B, C/0/C,\n A1/100/A', B1/85/B', C1/80/C'\n }{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_ueyha2s_9",
            title: "10. Hình hộp chữ nhật",
            description: "lăng trụ đứng",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=4; k=0.5;}]\n \\path\n (0:0) coordinate (A)\n (220:b) coordinate (B)\n (0:a) coordinate (D)\n (\$(B)+(D)-(A)\$) coordinate (C)\n ;\n \\foreach \\x in {A,B,C,D}{\n \\path (\\x)++(90:h) coordinate (\\x');\n }\n \\draw[dashed, line width=0.4pt] (A')--(A)--(B) (A)--(D);\n \\draw[line width=0.6pt]\n (B')--(A')--(D')--(C')\n (D')--(D)--(C)\n (B)--(C)--(C')--(B')--cycle\n ;\n \\\foreach \\p/\\goc in {\n A/170, B/-90, C/-90, D/0,\n A'/90, B'/90, C'/-25, D'/90\n }{\n \\draw (\\p) circle (0.4pt) node[shift={(\\goc:9pt)}]{\\$\\p\\$};\n };\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_kgloud_10",
            title: "11. Hình chóp tam giác",
            description: "đáy tam giác",
            code: `\\begin{tikzpicture}[declare function={a=5; b=2; h=3.5; k=0.5;}]\n \\path\n (0,0) coordinate (A)\n (0:a) coordinate (D)\n (-135:b) coordinate (B)\n (\$(B)+(0:b)\$) coordinate (C)\n (\$(A)+(90:h) \$)coordinate (S)\n ;\n \\path pic[draw, line width=0.6pt, angle radius=7pt]{right angle=B--A--S};\n \\path pic[draw, line width=0.6pt, angle radius=7pt]{right angle=D--A--S};\n \\draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);\n \\draw[line width=0.6pt]\n (S)--(B)--(C)--(D)--cycle\n (S)--(C)\n ;\n \\draw (A) circle (0.6pt) node[shift={(170:12pt)}]{\$A\$};\n \\foreach \\t/\\g in { B/-90, C/-90, D/0, S/90 left}{\n \\draw (\\t) circle (0.6pt) node[shift={(\\goc:8pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_p601ti_11",
            title: "12. Hình lăng trụ tam giác",
            description: "bản khác",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=4; k=0.5;}]\n \\path\n (0:0) coordinate (A)\n (-43:b) coordinate (B)\n (0:a) coordinate (C)\n ;\n \\foreach \\x in {A,B,C}{\n \\path (\\x)++(80:h) coordinate (\\x1);\n }\n \\draw[dashed, line width=0.4pt] (A)--(C);\n \\draw[line width=0.6pt]\n (B')--(A')--(C')--cycle\n (A')--(A)--(B)--(B')\n (C')--(C)--(B)\n ;\n \\foreach \\x/\\goc/\\t in {\n A/180/A, B/-90/B, C/0/C,\n A1/100/A', B1/85/B', C1/80/C'\n }{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_co1c8i_12",
            title: "13. Hình hộp chữ nhật",
            description: "phối cảnh",
            code: `\\begin{tikzpicture}[declare function={r=2.5; k=0.5;}]\n \\path\n (0:0) coordinate (A)\n (0:r) coordinate (B)\n (37:0.65*r) coordinate (D)\n (\$(B)+(D)-(A)\$) coordinate (C)\n ;\n \\foreach \\x in {A,B,C,D}{\n \\path (\\x)++(90:r) coordinate (\\x_1);\n }\n \\draw[dashed, line width=0.4pt] (D_1)--(D)--(A) (D)--(C);\n \\draw[line width=0.6pt]\n (A)--(B)--(C)\n (A)--(A_1)\n (B)--(B_1)\n (C)--(C_1)\n (A_1)--(B_1)--(C_1)--(D_1)--cycle\n ;\n \\foreach \\x/\\goc/\\t in {\n A/255/A, B/-75/B, C/10/C, D/170/D,\n A_1/135/A', B_1/90/B', C_1/45/C', D_1/90/D'\n }{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_e2fcs8_13",
            title: "14. Hình chóp có đáy hình bình hành",
            description: "tâm O",
            code: `\\begin{tikzpicture}[declare function={a=5; b=3; h=4.5; k=0.5;}]\n \\path\n (0,0) coordinate (A)\n (0:a) coordinate (D)\n (-135:b) coordinate (B)\n (\$(B)+(D)-(A)\$) coordinate (C)\n (\$(A)!k!(C)\$) coordinate (O)\n (\$(O)+(90:h)\$) coordinate (S)\n ;\n \\path pic[draw, line width=0.6pt, angle radius=6pt]{right angle=A--O--S};\n \\path pic[draw, line width=0.6pt, angle radius=6pt]{right angle=D--O--S};\n \\draw[dashed, line width=0.4pt] (B)--(A)--(D)--cycle (C)--(A)--(S)--(O);\n \\draw[line width=0.6pt]\n (S)--(B)--(C)--(D)--cycle\n (S)--(C)\n ;\n \\foreach \\t/\\g in {A/150, B/-90, C/-60, D/60, S/90, O/-90}{\n \\draw (\\t) circle (0.6pt) node[shift={(\\goc:8pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_5fgr4_14",
            title: "15. Hình lăng trụ đứng",
            description: "bản khác",
            code: `\\begin{tikzpicture}[declare function={a=4; b=2; h=a; k=0.5;}]\n \\path\n (0:0) coordinate (A)\n (220:b) coordinate (B)\n (0:a) coordinate (D)\n (\$(B)+(D)-(A)\$) coordinate (C)\n ;\n \\foreach \\x in {A,B,C,D}{\n \\path (\\x)++(90:h) coordinate (\\x');\n }\n \\draw[dashed, line width=0.4pt] (A')--(A)--(B) (A)--(D);\n \\draw[line width=0.6pt]\n (B')--(A')--(D')--(C')\n (D')--(D)--(C)\n (B)--(C)--(C')--(B')--cycle\n ;\n \\foreach \\x/\\goc/\\t in {\n A/170/A, B/-90/B, C/-90/C, D/0/D,\n A1/90/A', B1/90/B', C1/90/C', D1/90/D'\n }{\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\$\\t\$};\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_item_2uee3d_15",
            title: "16. Khối đa diện (8 đỉnh, 12 cạnh)",
            description: "mạng tinh thể",
            code: `\\begin{tikzpicture}[declare function={r=2.5; goc=30; k=0.5;}]\n \\foreach \\i in {1,...,3}{\n \\path (goc+\\i*120-120:r) coordinate (A_\\i);\n }\n \\foreach \\i in {1,...,3}{\n \\path (goc+\\i*120-60:r) coordinate (B_\\i);\n }\n \\foreach \\i in {1,...,6}{\n \\path (goc+\\i*60-60:1.5*r) coordinate (C_\\i);\n }\n \\draw[dash pattern=on 2pt off 2pt, line width=0.4pt]\n (B_1)--(B_2)--(B_3)--cycle\n (B_1)--(C_1) (B_1)--(C_2) (B_1)--(C_3)\n (B_2)--(C_3) (B_2)--(C_4) (B_2)--(C_5)\n (B_3)--(C_5) (B_3)--(C_6) (B_3)--(C_1)\n ;\n \\draw[line width=0.6pt]\n (A_1)--(A_2)--(A_3)--cycle\n (A_1)--(C_6) (A_1)--(C_1) (A_1)--(C_2)\n (A_2)--(C_2) (A_2)--(C_3) (A_2)--(C_4)\n (A_3)--(C_4) (A_3)--(C_5) (A_3)--(C_6)\n (C_1)--(C_2)--(C_3)--(C_4)--(C_5)--(C_6)--cycle\n ;\n \\foreach \\x in {A_1,A_2,A_3,B_1,B_2,B_3,C_1,C_2,C_3,C_4,C_5,C_6}{\n \\draw (\\x) circle (0.4pt);\n }\n\\end{tikzpicture}`,
          },
        ],
      },
      {
        name: "1.6. Mặt tròn xoay",
        templates: [
          {
            id: "rev-1",
            title: "1. Hình trụ",
            description: "Hình trụ tròn xoay.",
            code: `\\begin{tikzpicture}[declare function={theta=69; r=2; h=3.75;}, samples=150, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt] plot[domain=0:180] ({r*cos(\\x)},{r*sin(\\x)},0);
 \\draw[line width=0.6pt] plot[domain=180:360] ({r*cos(\\x)},{r*sin(\\x)},0) coordinate (A);
 \\draw[line width=0.6pt]
 (A)--+(0,0,h)
 (-r,0,0)--+(0,0,h)
 plot[domain=0:360] ({r*cos(\\x)},{r*sin(\\x)},h)
 ;
 \\path
 (0,0,0) coordinate (O)
 (0,0,h) coordinate (O')
 ($(A)+(0,0,h)$) coordinate (B)
 ;
 \\end{scope}
 \\draw[dashed, line width=0.4pt] (O')--(O)--(A);
 \\draw[line width=0.6pt] (O')--(B);
 \\path
 (O)--(A) node[pos=0.5, above, font=\\normalsize]{$r$}
 (A)--(B) node[pos=0.5, right, font=\\normalsize]{$\\ell$}
 (O)--(O') node[pos=0.5, left, font=\\normalsize]{$h$}
 (O')--(B) node[pos=0.5, above, font=\\normalsize]{$r$}
 ;
 \\foreach \\t/\\g/\\text in {O/180/O, O'/180/O', A/0/A, B/0/B}{
 \\draw (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\text$};
 }
\\end{tikzpicture}`,
          },
          {
            id: "rev-2",
            title: "2. Nón đỉnh ở trên",
            description: "Hình nón đỉnh S.",
            code: `\\begin{tikzpicture}[declare function={r=2.5; d=4; theta=70; tt=asin(r*cot(theta)/d); tth=180-tt; gqay=45;}, samples=150, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\begin{scope}[tdplot_main_coords]
 \\path
 (0,0,d) coordinate (S)
 (0,0,0) coordinate (O)
 ({r*cos(tt-gqay)},{r*sin(tt-gqay)},0) coordinate (M)
 ;
 \\draw[dashed, line width=0.4pt]
 (S)--(O)--(M)
 plot[domain=tt:tth] ({r*cos(\\x)},{r*sin(\\x)},0)
 ;
 \\draw[line width=0.6pt]
 plot[domain=tth:tt+360] ({r*cos(\\x)},{r*sin(\\x)},0)
 ({r*cos(tt)},{r*sin(tt)},0)--(S)--({r*cos(tth)},{r*sin(tth)},0)
 ;
 \\end{scope}
 \\draw[line width=0.6pt] (S)--(M) node[right, pos=0.65, font=\\normalsize]{$\\ell$};
 \\path
 (S)--(O) node[right, pos=0.5, font=\\normalsize]{$h$}
 (O)--(M) node[above, pos=0.5, font=\\normalsize]{$r$}
 ;
 \\foreach \\t/\\g/\\text in {S/90/S, O/180/O, M/-45/M}{
 \\draw (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\text$};
 }
\\end{tikzpicture}`,
          },
          {
            id: "rev-3",
            title: "3. Nón đỉnh ở dưới",
            description: "Hình nón ngược.",
            code: `\\begin{tikzpicture}[declare function={r=1.65; d=-4; theta=69; tt=asin(r*cot(theta)/d); tth=180-tt; gqay=45;}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\begin{scope}[tdplot_main_coords]
 \\draw[line width=0.6pt]
 plot[domain=0:360] ({r*cos(\\x)},{r*sin(\\x)},0)
 ({r*cos(tt)},{r*sin(tt)},0)--(0,0,d)--({r*cos(tth)},{r*sin(tth)},0)
 ;
 \\end{scope}
\\end{tikzpicture}`,
          },
          {
            id: "rev-4",
            title: "4. Mặt cầu",
            description: "Mặt cầu tâm O.",
            code: `\\begin{tikzpicture}[declare function={R=3; d=-1.5; theta=69; r=sqrt(R*R-d*d); betacrit=asin(d/r*cot(theta)); tgoc=320;}, samples=150, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\draw[line width=0.6pt] (0,0) coordinate (O) circle (R);
 \\begin{scope}[tdplot_main_coords]
 \\path ({R*cos(tgoc)},{R*sin(tgoc)},0) coordinate (M);
 \\draw[dashed, line width=0.4pt]
 plot[variable=\\t, domain=0:180] ({R*cos(\\t)},{R*sin(\\t)},0)
 (O)--(M) node[above, pos=0.5, font=\\normalsize]{$R$}
 ;
 \\draw[line width=0.6pt] plot[variable=\\t, domain=180:360] ({R*cos(\\t)},{R*sin(\\t)},0);
 \\end{scope}
 \\foreach \\t/\\g/\\text in {O/90/O, M/75/M}{
 \\draw (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\text$};
 }
\\end{tikzpicture}`,
          },
          {
            id: "rev-5",
            title: "5. Nón cụt",
            description: "Hình nón cụt.",
            code: `\\begin{tikzpicture}[declare function={r=3; rn=2; h=3; theta=70; d=(h*r)/(r-rn); tt=asin(r*cot(theta)/d); tth=180-asin(r*cot(theta)/d);}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 plot[domain=tt:tth] ({r*cos(\\x)},{r*sin(\\x)},0) coordinate (A)
 (r,0,0)--(0,0,0) coordinate (O) node[above, pos=0.5, font=\\normalsize]{$R$}--(0,0,h) coordinate (O') node[left, pos=0.5, font=\\normalsize]{$h$}--(rn,0,h) node[above, pos=0.5, font=\\normalsize]{$r$}
 ;
 \\draw[line width=0.6pt]
 plot[domain=tth:tt+360] ({r*cos(\\x)},{r*sin(\\x)},0) coordinate (B)
 plot[domain=tth:tt+360] ({rn*cos(\\x)},{rn*sin(\\x)},h) coordinate (Bt)
 plot[domain=tt:tth] ({rn*cos(\\x)},{rn*sin(\\x)},h) coordinate (At)
 ;
 \\end{scope}
 \\draw[line width=0.6pt] (A)--(At) (B)--(Bt);
 \\foreach \\t/\\g/\\text in {O/180/O, O'/180/O'}{
 \\draw (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\text$};
 }
\\end{tikzpicture}`,
          },
          {
            id: "rev-6",
            title: "6. Mặt cầu + Đường tròn",
            description: "Mặt cầu và đường tròn thiết diện.",
            code: `\\begin{tikzpicture}[declare function={R=3; d=-1.5; theta=69; r=sqrt(R*R-d*d); betacrit=asin(d/r*cot(theta)); tgoc=330;}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\draw[line width=0.6pt] (0,0) coordinate (O) circle (R);
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 (O)--(0,0,d) coordinate (H)--({r*cos(tgoc)},{r*sin(tgoc)},d) coordinate (M)--cycle
 plot[variable=\\t, domain=betacrit:180-betacrit] ({r*cos(\\t)},{r*sin(\\t)},d)
 plot[variable=\\t, domain=0:180] ({R*cos(\\t)},{R*sin(\\t)},0)
 ;
 \\draw[line width=0.6pt]
 plot[variable=\\t, domain=betacrit:-180-betacrit] ({r*cos(\\t)},{r*sin(\\t)},d)
 plot[variable=\\t, domain=180:360] ({R*cos(\\t)},{R*sin(\\t)},0)
 ;
 \\end{scope}
 \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=O--H--M};
 \\foreach \\t/\\g/\\text in {O/90/O, H/180/H, M/85/M}{
 \\draw (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\text$};
 }
\\end{tikzpicture}`,
          },
          {
            id: "rev-7",
            title: "7. Tròn xoay quanh Ox",
            description: "Thể tích khối tròn xoay quanh Ox.",
            code: `\\begin{tikzpicture}[>=stealth, declare function={xA=1; yA=1.5; xB=7; yB=3;}]
 \\draw[->, line width=0.6pt] (-1,0)--(xA-0.55,0) (xB,0)--(9,0) node[below right, font=\\normalsize]{$x$};
 \\draw[->, line width=0.6pt] (0,-3)--(0,3) node[left, font=\\normalsize]{$z$};
 \\draw[dashed, line width=0.4pt]
 (xA-0.5,0)--(xB,0)
 (xA,0) node[below, font=\\normalsize]{$a$}--(xA,yA) coordinate (A)
 (xB,0) node[below, font=\\normalsize]{$b$}--(xB,yB) coordinate (B)
 ;
 \\def\\curvef{(A).. controls+(60:2.5) and+(210:2.5)..(B)}
 \\begin{scope}[line width=0.6pt]
 \\draw \\curvef node[midway, above, font=\\normalsize]{$y=f(x)$};
 \\draw[transform canvas={yscale=-1}] \\curvef;
 \\draw (A) arc (90:270:{0.35*yA} and yA);
 \\draw[dashed, line width=0.4pt] (A) arc (90:-90:{0.35*yA} and yA);
 \\draw ($(B)+(0.1,0)$) arc (90:450:{0.35*yB} and yB);
 \\end{scope}
 \\draw[-latex, line width=0.6pt] (8.5,0)+(30:0.3) arc (30:330:0.2 and 0.3);
\\end{tikzpicture}`,
          },
          {
            id: "rev-9",
            title: "9. Tròn xoay quanh Oz",
            description: "Thể tích khối tròn xoay quanh Oz.",
            code: `\\begin{tikzpicture}[>=stealth, line width=0.6pt]
 \\def\\tpath{(1,0) to[out=50,in=-60] (0.55,2.5) to [out=120,in=-120] (0.75,5)}
 \\draw \\tpath;
 \\draw[xscale=-1] \\tpath;
 \\draw[dashed, line width=0.4pt] (1,0) arc (0:180:1 and 0.3);
 \\draw (0,5.03) ellipse (0.75 and 0.225);
 \\draw (1,0) arc (360:180:1 and 0.3);
 \\draw[dashed, line width=0.4pt, rotate=-10] (1,0)--(-1,0);
 \\draw[dashed, line width=0.4pt] (0,-0.3)--(0,5);
 \\draw[->, rotate=-10] (-2,0)--(-1,0) (1,0)--(2,0) node[above, font=\\normalsize]{$x$};
 \\draw[->] (0,-1)--(0,-.35) (0,5)--+(0,1) node[left, font=\\normalsize]{$z$};
 \\draw[-latex] ($(0,5.3)+(45:0.3)$) arc (45:315:0.3 and 0.125);
\\end{tikzpicture}`,
          },
          {
            id: "rev-10",
            title: "10. Trụ nội tiếp nón",
            description: "Hình trụ nội tiếp trong hình nón.",
            code: `\\begin{tikzpicture}[declare function={r=2.5; h=4; theta=70; tt=asin(r*cot(theta)/h); tth=180-asin(r*cot(theta)/h); rc=1.5; d=h-h*rc/r; ttc=asin(rc*cot(theta)/d); tthc=180-asin(rc*cot(theta)/d);}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 plot[domain=tt:tth] ({r*cos(\\x)},{r*sin(\\x)},0)
 plot[domain=ttc:tthc] ({rc*cos(\\x)},{rc*sin(\\x)},d)
 plot[domain=0:360] ({rc*cos(\\x)},{rc*sin(\\x)},0)
 (rc,0,0)--+(0,0,d) (-rc,0,0)--+(0,0,d)
 ;
 \\draw[line width=0.6pt]
 plot[domain=tthc:ttc+360] ({rc*cos(\\x)},{rc*sin(\\x)},d)
 plot[domain=tth:tt+360] ({r*cos(\\x)},{r*sin(\\x)},0)
 ({r*cos(tt)},{r*sin(tt)},0)--(0,0,h)--({r*cos(tth)},{r*sin(tth)},0)
 ;
 \\end{scope}
\\end{tikzpicture}`,
          },
          {
            id: "rev-11",
            title: "11. Trụ gắn nón",
            description: "Kết hợp hình trụ và hình nón.",
            code: `\\begin{tikzpicture}[declare function={r=2.5; h=4; theta=70; tt=asin(r*cot(theta)/h); tth=180-asin(r*cot(theta)/h); d=-3;}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 plot[domain=tt:tth] ({r*cos(\\x)},{r*sin(\\x)},0)
 plot[domain=tt:tth] ({r*cos(\\x)},{r*sin(\\x)},d)
 ;
 \\draw[line width=0.6pt]
 plot[domain=tth:tt+360] ({r*cos(\\x)},{r*sin(\\x)},d)
 plot[domain=tth:tt+360] ({r*cos(\\x)},{r*sin(\\x)},0)
 ({r*cos(tt)},{r*sin(tt)},0)--(0,0,h)--({r*cos(tth)},{r*sin(tth)},0)
 (r,0,0)--+(0,0,d)
 (-r,0,0)--+(0,0,d)
 ;
 \\end{scope}
\\end{tikzpicture}`,
          },
          {
            id: "rev-12",
            title: "12. Trụ nội tiếp cầu",
            description: "Hình trụ nội tiếp trong mặt cầu.",
            code: `\\begin{tikzpicture}[declare function={R=3; d=-1.75; theta=69; r=sqrt(R*R-d*d); betacrit=asin(d/r*cot(theta));}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\draw[line width=0.6pt] (0,0) coordinate (O) circle (R);
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 (r,0,d)--+(0,0,{-2*d})
 (-r,0,d)--+(0,0,{-2*d})
 plot[variable=\\t, domain=betacrit:180-betacrit] ({r*cos(\\t)},{r*sin(\\t)},d)
 plot[variable=\\t, domain=betacrit:-180-betacrit] ({r*cos(\\t)},{-r*sin(\\t)},-d)
 plot[variable=\\t, domain=0:180] ({R*cos(\\t)},{R*sin(\\t)},0)
 ;
 \\draw[line width=0.6pt]
 plot[variable=\\t, domain=betacrit:-180-betacrit] ({r*cos(\\t)},{r*sin(\\t)},d)
 plot[variable=\\t, domain=betacrit:180-betacrit] ({r*cos(\\t)},{-r*sin(\\t)},-d)
 plot[variable=\\t, domain=180:360] ({R*cos(\\t)},{R*sin(\\t)},0)
 ;
 \\end{scope}
\\end{tikzpicture}`,
          },
          {
            id: "rev-13",
            title: "13. Trụ ngoại tiếp cầu",
            description: "Hình trụ ngoại tiếp mặt cầu.",
            code: `\\begin{tikzpicture}[declare function={R=2.5; d=-1.75; theta=65;}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\draw[dashed, line width=0.4pt] (0,0) coordinate (O) circle (R);
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 plot[variable=\\t, domain=0:180] ({R*cos(\\t)},{R*sin(\\t)},0)
 plot[variable=\\t, domain=0:180] ({R*cos(\\t)},{R*sin(\\t)},-R)
 ;
 \\draw[line width=0.6pt]
 plot[variable=\\t, domain=180:360] ({R*cos(\\t)},{R*sin(\\t)},0)
 plot[variable=\\t, domain=180:360] ({R*cos(\\t)},{R*sin(\\t)},-R)
 plot[variable=\\t, domain=0:360] ({R*cos(\\t)},{R*sin(\\t)},R)
 (R,0,-R)--+(0,0,{2*R})
 (-R,0,-R)--+(0,0,{2*R})
 ;
 \\end{scope}
\\end{tikzpicture}`,
          },
          {
            id: "rev-14",
            title: "14. Nón nội tiếp cầu",
            description: "Hình nón nội tiếp trong mặt cầu.",
            code: `\\begin{tikzpicture}[declare function={R=3; d=-1.5; theta=69; r=sqrt(R*R-d*d); betacrit=asin(d/r*cot(theta)); tt=asin(r*cot(theta)/(R-d));}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\draw[line width=0.6pt] (0,0) coordinate (O) circle (R);
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 ({r*cos(tt)},{r*sin(tt)},d)--(0,0,R) coordinate (S)--({r*cos(180-tt)},{r*sin(180-tt)},d) coordinate (M)
 plot[variable=\\t, domain=betacrit:180-betacrit] ({r*cos(\\t)},{r*sin(\\t)},d)
 plot[variable=\\t, domain=0:180] ({R*cos(\\t)},{R*sin(\\t)},0)
 ;
 \\draw[line width=0.6pt]
 plot[variable=\\t, domain=betacrit:-180-betacrit] ({r*cos(\\t)},{r*sin(\\t)},d)
 plot[variable=\\t, domain=180:360] ({R*cos(\\t)},{R*sin(\\t)},0)
 ;
 \\end{scope}
\\end{tikzpicture}`,
          },
          {
            id: "rev-15",
            title: "15. Cầu nội tiếp nón",
            description: "Mặt cầu nội tiếp trong hình nón.",
            code: `\\begin{tikzpicture}[declare function={rc=2.5; d=4; l=sqrt(rc*rc+d*d); theta=69; tt=asin(rc*cot(theta)/d); tth=180-asin(rc*cot(theta)/d); rs=1.5; h=d-rs*l/rc;}, samples=200, smooth]
 \\tdplotsetmaincoords{theta}{0}
 \\begin{scope}[tdplot_main_coords]
 \\draw[dashed, line width=0.4pt]
 plot[domain=tt:tth] ({rc*cos(\\x)},{rc*sin(\\x)},0)
 plot[domain=0:360] ({rs*cos(\\x)},{rs*sin(\\x)},h)
 ;
 \\draw[line width=0.6pt]
 plot[domain=tth:tt+360] ({rc*cos(\\x)},{rc*sin(\\x)},0)
 ({rc*cos(tt)},{rc*sin(tt)},0)--(0,0,d)--({rc*cos(tth)},{rc*sin(tth)},0)
 ;
 \\path (0,0,h) coordinate (O);
 \\end{scope}
 \\draw[dashed, line width=0.4pt] (O) circle (rs);
\\end{tikzpicture}`,
          },
          {
            id: "rev-16",
            title: "16. Giao trụ và MP",
            description: "Giao tuyến giữa hình trụ và mặt phẳng.",
            code: `\\begin{tikzpicture}[declare function={r=4; h=2; rnt=r*sin(30); theta=70; phi=-145; nA=h*(sin(240)-sin(120)); nB=h*(-cos(240)+cos(120)); nC=r*(-sin(240)+2*sin(120)); tt=phi; tth=180+tt;}]
 \\tdplotsetmaincoords{theta}{phi}
 \\begin{scope}[tdplot_main_coords]
 \\path
 (r,0,0) coordinate (A)
 ({r*cos(120)},{r*sin(120)},0) coordinate (B)
 ({r*cos(240)},{r*sin(240)},0) coordinate (C)
 (r,0,{2*h}) coordinate (Ap)
 ({r*cos(120)},{r*sin(120)},{2*h}) coordinate (Bp)
 ({r*cos(240)},{r*sin(240)},{2*h}) coordinate (Cp)
 ($(C)!0.5!(Cp)$) coordinate (M)
 ($(B)!0.5!(Bp)$) coordinate (N)
 ;
 \\draw[line width=0.6pt]
 (A)--(B)--(C) (Ap)--(A) (B)--(Bp) (C)--(Cp)
 (Ap)--(Bp)--(Cp)--cycle (Ap)--(N)--(M)
 ;
 \\draw[dashed, line width=0.4pt] plot[domain=0:360, samples=200] ({rnt*cos(\\x)},{rnt*sin(\\x)},0) (A)--(C) (Ap)--(M);
 \\draw[dashed, line width=0.4pt] plot[domain=0:360, samples=200] ({rnt*cos(\\x)},{rnt*sin(\\x)},{(-nA*(rnt*cos(\\x)-r)-nB*rnt*sin(\\x))/nC+2*h});
 \\draw[dashed, line width=0.4pt]
 ({rnt*cos(tt)},{rnt*sin(tt)},0)--({rnt*cos(tt)},{rnt*sin(tt)},{(-nA*(rnt*cos(tt)-r)-nB*rnt*sin(tt))/nC+2*h})
 ({rnt*cos(tth)},{rnt*sin(tth)},0)--({rnt*cos(tth)},{rnt*sin(tth)},{(-nA*(rnt*cos(tth)-r)-nB*rnt*sin(tth))/nC+2*h})
 ;
 \\end{scope}
 \\foreach \\t/\\g/\\text in {A/180/A, B/-60/B, C/0/C, M/10/M, N/-20/N}{
 \\draw (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\text$};
 }
 \\foreach \\t/\\g/\\d in {Bp/80/B', Ap/120/A', Cp/30/C'}{
 \\draw (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\d$};
 }
\\end{tikzpicture}`,
          },
          {
            id: "hinh-tru-h16",
            title: `Hình trụ (H16)`,
            description: `Hình trụ (hình học không gian)`,
            code: String.raw`\begin{tikzpicture}[every node/.style={font=\normalsize}]
 \draw[line width=0.6pt] (-1,2) -- (-1,0) arc (180:360:1 and 0.2) -- (1,2);
 \draw (-1,2) ellipse (1 and 0.2);
 \fill[cyan!30] (-1,0.5) -- (-1,0) arc (180:360:1 and 0.2) -- (1,0.5) -- cycle;
 \draw[dashed, line width=0.4pt] (0,0) ellipse (1 and 0.2);
\end{tikzpicture}`,
          },
        ],
      },
      {
        name: "1.7. Bảng biến thiên - Đồ thị",
        templates: [
          {
            id: "dyn_graph_upd_0",
            title: "1. Bảng biến thiên hàm bậc hai",
            description: "f(x)=x^2-3x+2",
            code: `\\begin{tikzpicture}[\n scale=1,\n >=stealth,\n line join=round,\n every node/.style={font=\\normalsize},\n declare function={f(\\x)=\\x^2-3*\\x+2;}\n]\n \\tkzTabInit[nocadre=false, lgt=1.5, espcl=2.5, deltacl=0.6]\n {\$x\$/0.7, \$f'(x)\$/0.7}\n {\$-\\infty\$, \$1\$, \$2\$, \$+\\infty\$}\n \\tkzTabLine{, +, 0, -, 0, +, }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_graph_upd_1",
            title: "2. Bảng biến thiên hàm phân thức",
            description: "f(x)=(x-2)/(x-1)",
            code: `\\begin{tikzpicture}[\nscale=0.8,\nevery node/.style={font=\\normalsize},\ndeclare function={f(\\x)=(\\x-2)/(\\x-1);}]\n\\tkzTabInit[nocadre=false, lgt=1.2, espcl=3.5, deltacl=0.6]\n{\$x\$/0.7, \$f'(x)\$/0.7, \$f(x)\$/2}\n{\$-\\infty\$, \$1\$, \$+\\infty\$}\n\\tkzTabLine{, +, , +, }\n\\draw[double distance=1pt, double=white, line width=0.6pt] (N21) -- (N23);\n\\path\n([yshift=16pt]N13) node (A') {\$1\$}\n([xshift=-16pt, yshift=-8pt]N22) node (A2) {\$+\\infty\$}\n([xshift=16pt, yshift=8pt]N23) node (A3) {\$-\\infty\$}\n([yshift=-16pt]N32) node (A4) {\$1\$};\n\\foreach \\i/\\j in {1/2, 3/4} {\n \\draw[-Stealth, line width=0.6pt] (A\\i) -- (A\\j);\n}\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_graph_upd_2",
            title: "3. Bảng biến thiên hàm bậc ba",
            description: "f(x)=x^3-3x^2+1 có mũi tên",
            code: `\\begin{tikzpicture}[\n scale=1,\n >=stealth,\n line join=round,\n every node/.style={font=\\normalsize},\n declare function={f(\\x)=\\x*\\x*\\x-3*\\x^2+1;}\n]\n \\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.6]\n {\$x\$/0.7, \$y'\$/0.7, \$y\$/2.5}\n {\$-\\infty\$, \$0\$, \$2\$, \$+\\infty\$}\n \\tkzTabLine{, +, 0, -, 0, +, }\n % Các điểm giá trị\n \\path\n ([yshift=8pt]N13) node (A') {\$-\\infty\$}\n ([yshift=-8pt]N22) node (A2) {\$1\$}\n ([yshift=-50pt]N32) node (A3) {\$-3\$}\n ([yshift=-8pt]N42) node (A4) {\$+\\infty\$};\n % Mũi tên liên kết\n \\foreach \\i/\\j in {1/2, 2/3, 3/4} {\n \\draw[-Stealth, line width=0.6pt] (A\\i) -- (A\\j);\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_graph_upd_3",
            title: "4. Bảng biến thiên hàm phân thức",
            description: "f(x)=(x^2-2x+2)/(x-1)",
            code: `\\begin{tikzpicture}[\n scale=1,\n >=stealth,\n line join=round,\n every node/.style={font=\\normalsize},\n declare function={f(\\x)=(\\x*\\x-2*\\x+2)/(\\x-1);}\n]\n \\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.6]\n {\$x\$/0.7, \$y'\$/0.7, \$y\$/2.5}\n {\$-\\infty\$, \$0\$, \$1\$, \$2\$, \$+\\infty\$}\n \\tkzTabLine{, +, 0, -, , -, 0, +, }\n % Đường đôi che dấu\n \\draw[double distance=1pt, double=white, line width=0.6pt] (N31) -- (N33);\n % Các điểm giá trị\n \\path\n ([yshift=8pt]N13) node (A') {\$-\\infty\$}\n ([yshift=-8pt]N22) node (A2) {\$-2\$}\n ([xshift=-16pt, yshift=8pt]N33) node (A3) {\$-\\infty\$}\n ([xshift=16pt, yshift=-8pt]N32) node (A4) {\$+\\infty\$}\n ([yshift=8pt]N43) node (A5) {\$2\$}\n ([yshift=-8pt]N52) node (A6) {\$+\\infty\$};\n % Mũi tên liên kết\n \\foreach \\i/\\j in {1/2, 2/3, 4/5, 5/6} {\n \\draw[-Stealth, line width=0.6pt] (A\\i) -- (A\\j);\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_graph_upd_4",
            title: "5. Bảng biến thiên hàm căn thức",
            description: "f(x)=sqrt(x^2-4x+3)",
            code: `\\begin{tikzpicture}[\n scale=1,\n >=stealth,\n line join=round,\nevery node/.style={font=\\normalsize},\n declare function={f(\\x)=sqrt(\\x*\\x-4*\\x+3);}\n]\n \\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.6]\n {\$x\$/0.7, \$y'\$/0.7, \$y\$/2.5}\n {\$-\\infty\$, \$1\$, \$3\$, \$+\\infty\$}\n \\tkzTabLine{, -, , , , +, }\n % Vùng không xác định (gạch chéo)\n \\draw[\n pattern={Lines[angle=45, distance=3pt, line width=0.3pt]},\n pattern color=gray,\n line width=0.6pt\n ] (N21) rectangle (N33);\n % Đường trắng che các đường kẻ\n \\draw[white, line width=1pt] (N23) -- (N33);\n \\draw[white, line width=1pt] (N22) -- (N23);\n \\draw[white, line width=1pt] (N32) -- (N33);\n % Đường đôi\n \\draw[double distance=1pt, double=white, line width=0.6pt] (N21) -- (N22);\n \\draw[double distance=1pt, double=white, line width=0.6pt] (N31) -- (N32);\n % Các điểm giá trị\n \\path\n ([yshift=-8pt]N12) node (A') {\$+\\infty\$}\n ([yshift=8pt]N23) node[fill=white, inner sep=2pt] (A2) {\$0\$}\n ([yshift=8pt]N33) node[fill=white, inner sep=2pt] (A3) {\$0\$}\n ([yshift=-8pt]N42) node (A4) {\$+\\infty\$};\n % Mũi tên liên kết\n \\foreach \\i/\\j in {1/2, 3/4} {\n \\draw[-Stealth, line width=0.6pt] (A\\i) -- (A\\j);\n }\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_graph_upd_5",
            title: "6. Đồ thị hàm bậc ba",
            description: "f(x)=x^3-3x^2+1",
            code: `\\begin{tikzpicture}[\n scale=1,\n >=stealth,\n line join=round,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x)=\\x*\\x*\\x - 3*\\x*\\x + 1;\n xmin=-1.5;\n xmax=3.5;\n ymin=-4.5;\n ymax=2.5;\n }\n]\n % Trục tọa độ\n \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {\$x\$};\n \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[left] {\$y\$};\n % Điểm O\n \\fill (0,0) circle (0.4pt) node[below right] {\$O\$};\n % Đồ thị\n \\begin{scope}\n \\clip (xmin, ymin) rectangle (xmax, ymax);\n \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:xmax] plot (\\x, {f(\\x)});\n \\end{scope}\n % Các điểm đặc biệt\n \\fill (0, 1) circle (0.4pt) node[above left] {\$1\$};\n % Điểm (2, -3)\n \\draw[dashed, line width=0.4pt] (2, 0) -- (2, -3) -- (0, -3);\n \\fill (2, -3) circle (0.4pt);\n \\fill (2, 0) circle (0.4pt) node[above] {\$2\$};\n \\fill (0, -3) circle (0.4pt) node[left] {\$-3\$};\n\\end{tikzpicture}`,
          },
          {
            id: "dyn_graph_upd_6",
            title: "7. Đồ thị hàm phân thức",
            description: "f(x)=(x^2-2x+2)/(x-1) và tiệm cận",
            code: `\\begin{tikzpicture}[\n scale=1,\n >=stealth,\n line join=round,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x)=(\\x*\\x - 2*\\x + 2)/(\\x - 1);\n tcx(\\x)=\\x - 1;\n xmin=-3.2;\n xmax=5.2;\n ymin=-4.5;\n ymax=4.5;\n }\n]\n % Trục tọa độ\n \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {\$x\$};\n \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[left] {\$y\$};\n % Điểm O\n \\fill (0,0) circle (0.4pt) node[below left] {\$O\$};\n % Đồ thị\n \\begin{scope}\n \\clip (xmin, ymin) rectangle (xmax, ymax);\n % Tiệm cận đứng x=1\n \\draw[dashed, line width=0.4pt] (1, ymin) -- (1, ymax);\n % Tiệm cận xiên y=x-1\n \\draw[dashed, line width=0.4pt, domain=xmin:xmax] plot (\\x, {tcx(\\x)});\n % Nhánh trái\n \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:0.9] plot (\\x, {f(\\x)});\n % Nhánh phải\n \\draw[line width=0.6pt, smooth, samples=300, domain=1.1:xmax] plot (\\x, {f(\\x)});\n \\end{scope}\n % Các điểm đặc biệt\n \\fill (0, -2) circle (0.4pt) node[left] {\$-2\$};\n \\fill (2, 2) circle (0.4pt);\n \\draw[dashed, line width=0.4pt] (2, 0) -- (2, 2) -- (0, 2);\n \\fill (0, 2) circle (0.4pt) node[left] {\$2\$};\n \\fill (2, 0) circle (0.4pt) node[below] {\$2\$};\n \\fill (1, 0) circle (0.4pt) node[above right] {\$1\$};\n\\end{tikzpicture}`,
          },
        ],
      },
      {
        name: "1.8. Tô miền diện tích",
        templates: [
          {
            id: "shading-1",
            title: "1. DIỆN TÍCH HÌNH PHẲNG GIỮA HÀM BẬC 3 VÀ ĐƯỜNG THẲNG",
            description: "1. DIỆN TÍCH HÌNH PHẲNG GIỮA HÀM BẬC 3 VÀ ĐƯỜNG THẲNG",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = \\x*\\x*\\x - 3*\\x;\n g(\\x) = \\x;\n xmin = -2.5; xmax = 2.5;\n ymin = -3.5; ymax = 3.5;\n x1 = -2; x2 = 0; x3 = 2;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=blue!60]\n plot[domain=x1:x2, smooth] (\\x, {f(\\x)}) --\n plot[domain=x1:x2, smooth] (\\x, {g(\\x)}) -- cycle;\n \n \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=red!60]\n plot[domain=x2:x3, smooth] (\\x, {g(\\x)}) --\n plot[domain=x2:x3, smooth] (\\x, {f(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, above] {$y=x^3-3x$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=2, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=x$};}}, decorate}\n]\n plot (\\x, {g(\\x)});\n\\end{scope}\n\\foreach \\i in {x1, x2, x3} \\fill (\\i,{g(\\i)}) circle (1.2pt);\n\\draw[dashed, line width=0.6pt] (x1,0) node[above left] {$x_1$} -- (x1,{g(x1)});\n\\draw[dashed, line width=0.6pt] (x3,0) node[below right] {$x_2$} -- (x3,{g(x3)});\n\\end{tikzpicture}"
          },
          {
            id: "shading-2",
            title: "2. DIỆN TÍCH DƯỚI ĐƯỜNG CONG SINE",
            description: "2. DIỆN TÍCH DƯỚI ĐƯỜNG CONG SINE",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1.5,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = sin(deg(\\x));\n xmin = -0.5; xmax = 3.5;\n ymin = -1.2; ymax = 1.2;\n a = 0; b = pi;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \n \\fill[pattern={Lines[angle=60, distance=3.5pt, line width=0.3pt]}, pattern color=teal!70]\n plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) -- (b,0) -- (a,0) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.35 with {\\node[transform shape, sloped, above] {$y=\\sin x$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n\\end{scope}\n\\fill (b,0) circle (0.4pt) node[below] {$\\pi$};\n\\end{tikzpicture}"
          },
          {
            id: "shading-3",
            title: "3. TÍNH ĐỐI XỨNG CỦA HÀM MŨ VÀ LOGARIT",
            description: "3. TÍNH ĐỐI XỨNG CỦA HÀM MŨ VÀ LOGARIT",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = exp(\\x);\n g(\\x) = ln(\\x);\n h(\\x) = \\x;\n xmin = -1.5; xmax = 4.5;\n ymin = -1.5; ymax = 4.5;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.7 with {\\node[transform shape, sloped, above] {$y=e^x$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=100, domain=0.01:xmax,\n postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, below] {$y=\\ln x$};}}, decorate}\n]\n plot (\\x, {g(\\x)});\n \\draw[dashed, line width=0.5pt, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.9 with {\\node[transform shape, sloped, above] {$y=x$};}}, decorate}\n]\n plot (\\x, {h(\\x)});\n\\end{scope}\n\\end{tikzpicture}"
          },
          {
            id: "shading-4",
            title: "4. ĐỒ THỊ VÀ TIẾP TUYẾN",
            description: "4. ĐỒ THỊ VÀ TIẾP TUYẾN",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1.2,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = -0.5*\\x*\\x + 2*\\x + 1;\n df(\\x) = -\\x + 2;\n x0 = 3;\n y0 = f(x0);\n tangent(\\x) = df(x0)*(\\x - x0) + y0;\n xmin = -1.5; xmax = 5.5;\n ymin = -1; ymax = 4.5;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.25 with {\\node[transform shape, sloped, above] {$y=f(x)$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above] {$d$};}}, decorate}\n]\n plot (\\x, {tangent(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.6pt] (x0,0) node[below] {$x_0$} -- (x0,y0) -- (0,y0) node[left] {$y_0$};\n\\fill (x0,y0) circle (1.2pt) node[above right] {$M$};\n\\end{tikzpicture}"
          },
          {
            id: "shading-5",
            title: "5. DIỆN TÍCH GIỮA HAI PARABOL",
            description: "5. DIỆN TÍCH GIỮA HAI PARABOL",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = -\\x*\\x + 4;\n g(\\x) = \\x*\\x - 2*\\x;\n xmin = -2.5; xmax = 3.5;\n ymin = -2.5; ymax = 5.5;\n a = -1; b = 2;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=60, distance=3pt, line width=0.3pt]}, pattern color=orange!70]\n plot[domain=a:b, smooth] (\\x, {f(\\x)}) --\n plot[domain=b:a, smooth] (\\x, {g(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=-x^2+4$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, below] {$y=x^2-2x$};}}, decorate}\n]\n plot (\\x, {g(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.6pt] (a,0) node[below] {$a$} -- (a,{f(a)});\n\\draw[dashed, line width=0.6pt] (b,0) node[below] {$b$} -- (b,{f(b)});\n\\fill (a,{f(a)}) circle (1.2pt);\n\\fill (b,{f(b)}) circle (1.2pt);\n\\end{tikzpicture}"
          },
          {
            id: "shading-6",
            title: "6. PARABOL VÀ TRỤC HOÀNH (Dạng cơ bản nhất)",
            description: "6. PARABOL VÀ TRỤC HOÀNH (Dạng cơ bản nhất)",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = -\\x*\\x + 4;\n xmin = -2.5; xmax = 2.5;\n ymin = -1; ymax = 5;\n a = -2; b = 2;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=orange!70]\n plot[domain=a:b, smooth] (\\x, {f(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.35 with {\\node[transform shape, sloped, above] {$y=-x^2+4$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n\\end{scope}\n\\foreach \\i in {a, b} \\fill (\\i,0) circle (1.2pt) node[below] {$\\i$};\n\\end{tikzpicture}"
          },
          {
            id: "shading-7",
            title: "7. HÀM BẬC 3 CẮT TRỤC HOÀNH (Phân tích dấu 2 miền)",
            description: "7. HÀM BẬC 3 CẮT TRỤC HOÀNH (Phân tích dấu 2 miền)",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=0.8,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = \\x*\\x*\\x - 4*\\x;\n xmin = -2.5; xmax = 2.5;\n ymin = -4.5; ymax = 4.5;\n x1 = -2; x2 = 0; x3 = 2;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \n \\fill[pattern={Lines[angle=60, distance=3pt, line width=0.3pt]}, pattern color=blue!60]\n plot[domain=x1:x2, smooth] (\\x, {f(\\x)}) -- cycle;\n \n \\fill[pattern={Lines[angle=120, distance=3pt, line width=0.3pt]}, pattern color=red!60]\n plot[domain=x2:x3, smooth] (\\x, {f(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, above] {$y=x^3-4x$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n\\end{scope}\n\\foreach \\i in {x1, x3} \\fill (\\i,0) circle (1.2pt) node[above] {$\\i$};\n\\end{tikzpicture}"
          },
          {
            id: "shading-8",
            title: "8. HAI ĐƯỜNG CONG CƠ BẢN",
            description: "8. HAI ĐƯỜNG CONG CƠ BẢN",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=3,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = sqrt(abs(\\x));\n g(\\x) = \\x*\\x;\n xmin = -0.2; xmax = 1.3;\n ymin = -0.2; ymax = 1.3;\n a = 0; b = 1;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.5pt) node[shift={(-135:8pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=45, distance=2pt, line width=0.3pt]}, pattern color=purple!70]\n plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) --\n plot[domain=b:a, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=0:xmax,\n postaction={decoration={markings, mark=at position 0.6 with {\\node[transform shape, sloped, above] {$y=\\sqrt{x}$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, below right] {$y=x^2$};}}, decorate}\n]\n plot (\\x, {g(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.4pt] (b,0) node[below] {$1$} -- (b,{f(b)}) -- (0,{f(b)}) node[left] {$1$};\n\\fill (b,{f(b)}) circle (0.5pt);\n\\end{tikzpicture}"
          },
          {
            id: "shading-9",
            title: "9. HÀM LƯỢNG GIÁC GIAO NHAU",
            description: "9. HÀM LƯỢNG GIÁC GIAO NHAU",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=2,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = sin(deg(\\x));\n g(\\x) = cos(deg(\\x));\n xmin = -0.3; xmax = 1.8;\n ymin = -0.3; ymax = 1.3;\n x1 = 0; x2 = pi/4; x3 = pi/2;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.6pt) node[shift={(-135:8pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=60, distance=2.5pt, line width=0.3pt]}, pattern color=teal!70]\n plot[domain=x1:x2, smooth, samples=100] (\\x, {g(\\x)}) --\n plot[domain=x2:x1, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;\n \\fill[pattern={Lines[angle=120, distance=2.5pt, line width=0.3pt]}, pattern color=cyan!70]\n plot[domain=x2:x3, smooth, samples=100] (\\x, {f(\\x)}) --\n plot[domain=x3:x2, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.65 with {\\node[transform shape, sloped, above] {$y=\\sin x$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=\\cos x$};}}, decorate}\n]\n plot (\\x, {g(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.5pt] (x2,0) node[below] {$\\frac{\\pi}{4}$} -- (x2,{f(x2)});\n\\draw[dashed, line width=0.5pt] (x3,0) node[below] {$\\frac{\\pi}{2}$} -- (x3,{f(x3)});\n\\fill (x2,{f(x2)}) circle (0.6pt);\n\\end{tikzpicture}"
          },
          {
            id: "shading-10",
            title: "10. ỨNG DỤNG LOGARIT NÊ-PE",
            description: "10. ỨNG DỤNG LOGARIT NÊ-PE",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1.5,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = 1/\\x;\n xmin = -0.5; xmax = 3.5;\n ymin = -0.5; ymax = 2.5;\n a = 1; b = 2.718;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!80]\n plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) -- (b,0) -- (a,0) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=200, domain=0.4:xmax,\n postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=\\frac{1}{x}$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.6pt] (a,0) node[below] {$1$} -- (a,{f(a)});\n\\draw[dashed, line width=0.6pt] (b,0) node[below] {$e$} -- (b,{f(b)});\n\\fill (a,{f(a)}) circle (0.4pt);\n\\fill (b,{f(b)}) circle (0.4pt);\n\\end{tikzpicture}"
          },
          {
            id: "shading-11",
            title: "11. HÀM SỐ MŨ",
            description: "11. HÀM SỐ MŨ",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1.5,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = exp(\\x);\n g(\\x) = exp(-\\x);\n xmin = -1; xmax = 1.5;\n ymin = -0.5; ymax = 3.5;\n a = 0; b = 1;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=magenta!70]\n plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) --\n plot[domain=b:a, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.75 with {\\node[transform shape, sloped, above left] {$y=e^x$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, above right] {$y=e^{-x}$};}}, decorate}\n]\n plot (\\x, {g(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.6pt] (b,0) node[below] {$1$} -- (b,{f(b)});\n\\fill (0,1) circle (0.4pt) node[left] {$1$};\n\\end{tikzpicture}"
          },
          {
            id: "shading-12",
            title: "12. ĐỒ THỊ, TIẾP TUYẾN VÀ TRỤC TUNG",
            description: "12. ĐỒ THỊ, TIẾP TUYẾN VÀ TRỤC TUNG",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1.5,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = \\x*\\x + 1;\n df(\\x) = 2*\\x;\n x0 = 1; y0 = 2;\n tangent(\\x) = df(x0)*(\\x - x0) + y0;\n xmin = -0.5; xmax = 2;\n ymin = -0.5; ymax = 3.5;\n a = 0; b = 1;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=violet!70]\n plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) --\n plot[domain=b:a, smooth, samples=100] (\\x, {tangent(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.65 with {\\node[transform shape, sloped, above] {$y=x^2+1$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.7 with {\\node[transform shape, sloped, below right] {$y=2x$};}}, decorate}\n]\n plot (\\x, {tangent(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.6pt] (b,0) node[below] {$1$} -- (b,y0) -- (0,y0) node[left] {$2$};\n\\fill (b,y0) circle (0.4pt);\n\\fill (0,1) circle (0.4pt) node[above left] {$1$};\n\\end{tikzpicture}"
          },
          {
            id: "shading-13",
            title: "13. HÀM BẬC BỐN TRÙNG PHƯƠNG CẮT OX",
            description: "13. HÀM BẬC BỐN TRÙNG PHƯƠNG CẮT OX",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=0.8,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = -\\x*\\x*\\x*\\x + 5*\\x*\\x - 4;\n xmin = -2.5; xmax = 2.5;\n ymin = -5; ymax = 3.5;\n x1 = -2; x2 = -1; x3 = 1; x4 = 2;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=brown!80]\n plot[domain=x1:x2, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;\n \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=olive!80]\n plot[domain=x2:x3, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;\n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=brown!80]\n plot[domain=x3:x4, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=150, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.73 with {\\node[transform shape, sloped, below right] {$y=-x^4+5x^2-4$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n\\end{scope}\n\\foreach \\i in {x1, x2, x3, x4} \\fill (\\i,0) circle (1.2pt) node[above right] {$\\i$};\n\\end{tikzpicture}"
          },
          {
            id: "shading-14",
            title: "14. HÀM CHỨA DẤU GIÁ TRỊ TUYỆT ĐỐI",
            description: "14. HÀM CHỨA DẤU GIÁ TRỊ TUYỆT ĐỐI",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=0.8,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = abs(\\x*\\x - 1);\n g(\\x) = 3;\n xmin = -2.5; xmax = 2.5;\n ymin = -1; ymax = 4.5;\n a = -2; b = 2;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n \\fill[pattern={Lines[angle=60, distance=3pt, line width=0.3pt]}, pattern color=yellow!60!black]\n plot[domain=a:b, smooth, samples=300] (\\x, {f(\\x)}) -- (b,3) -- (a,3) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.27 with {\\node[transform shape, sloped, above] {$y=|x^2-1|$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt] (xmin,3) -- (xmax,3) node[above left] {$y=3$};\n\\end{scope}\n\\draw[dashed, line width=0.6pt] (a,0) node[below] {$-2$} -- (a,3);\n\\draw[dashed, line width=0.6pt] (b,0) node[below] {$2$} -- (b,3);\n\\fill (a,3) circle (1.2pt);\n\\fill (b,3) circle (1.2pt);\n\\end{tikzpicture}"
          },
          {
            id: "shading-15",
            title: "15. HÌNH PHẲNG PHỨC TẠP GIỚI HẠN BỞI 3 ĐƯỜNG",
            description: "15. HÌNH PHẲNG PHỨC TẠP GIỚI HẠN BỞI 3 ĐƯỜNG",
            code: "\\begin{tikzpicture}[\n >=stealth, line join=round, scale=1.5,\n every node/.style={font=\\normalsize},\n declare function={\n f(\\x) = sqrt(abs(\\x));\n g(\\x) = \\x - 2;\n xmin = -0.5; xmax = 4.5;\n ymin = -1; ymax = 2.5;\n x1 = 0; x2 = 2; x3 = 4;\n }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};\n\\begin{scope}\n \\clip (xmin,ymin) rectangle (xmax,ymax);\n % Tô miền 1: Dưới f(x) từ 0 đến 2\n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=teal!70]\n plot[domain=x1:x2, smooth, samples=100] (\\x, {f(\\x)}) -- (x2,0) -- (x1,0) -- cycle;\n \n % Tô miền 2: Giữa f(x) và g(x) từ 2 đến 4\n \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=teal!70]\n plot[domain=x2:x3, smooth, samples=100] (\\x, {f(\\x)}) --\n plot[domain=x3:x2, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;\n \\draw[line width=0.6pt, smooth, samples=200, domain=0:xmax,\n postaction={decoration={markings, mark=at position 0.5 with {\\node[transform shape, sloped, above] {$y=\\sqrt{x}$};}}, decorate}\n]\n plot (\\x, {f(\\x)});\n \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,\n postaction={decoration={markings, mark=at position 0.6 with {\\node[transform shape, sloped, below right] {$y=x-2$};}}, decorate}\n]\n plot (\\x, {g(\\x)});\n\\end{scope}\n\\draw[dashed, line width=0.6pt] (x3,0) node[below] {$4$} -- (x3,{f(x3)});\n\\fill (x2,0) circle (0.4pt) node[below right] {$2$};\n\\fill (x3,{f(x3)}) circle (0.4pt);\n\\end{tikzpicture}"
          }
          ,{
            id: "shading-16",
            title: "16. Diện tích giữa 2 đồ thị",
            description: "Diện tích giữa 2 đồ thị và 2 đường thẳng x=a, x=b",
            code: "\\begin{tikzpicture}[\n  >=stealth, line join=round, line cap=round,\n  every node/.style={font=\\normalsize},\n  declare function={\n    f(\\x) = \\x*\\x*\\x - 3*\\x + 1;\n    g(\\x) = -\\x*\\x + 1;\n    xmin = -3; xmax = 2.5;\n    ymin = -5.5; ymax = 4.5;\n    x1 = (-1 - sqrt(13))/2;\n    x2 = 0;\n    x3 = (-1 + sqrt(13))/2;\n  }\n]\n\\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};\n\n\\begin{scope}\n  \\clip (xmin, ymin) rectangle (xmax, ymax);\n  \n  \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=teal]\n    plot[domain=x1:x2, smooth, samples=150] (\\x, {f(\\x)}) --\n    plot[domain=x2:x1, smooth, samples=150] (\\x, {g(\\x)}) -- cycle;\n    \n  \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=orange]\n    plot[domain=x2:x3, smooth, samples=150] (\\x, {g(\\x)}) --\n    plot[domain=x3:x2, smooth, samples=150] (\\x, {f(\\x)}) -- cycle;\n    \n  \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:xmax,\n    postaction={decoration={markings, mark=at position 0.86 with {\\node[transform shape, sloped, above left] {$y=x^3-3x+1$};}}, decorate}]\n    plot (\\x, {f(\\x)});\n    \n  \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:xmax,\n    postaction={decoration={markings, mark=at position 0.82 with {\\node[transform shape, sloped, below right] {$y=-x^2+1$};}}, decorate}]\n    plot (\\x, {g(\\x)});\n\\end{scope}\n\n\\draw[dashed, line width=0.4pt] (x1, {g(x1)}) -- (180:{-x1});\n\\draw[dashed, line width=0.4pt] (x3, {g(x3)}) -- (0:x3);\n\n\\fill (0,0) circle (0.8pt) node[shift={(-135:10pt)}] {$O$};\n\\fill (x1, {g(x1)}) circle (0.8pt);\n\\fill (180:{-x1}) circle (0.8pt) node[above] {$x_1$};\n\\fill (90:1) circle (0.8pt) node[shift={(45:10pt)}] {$1$};\n\\fill (x3, {g(x3)}) circle (0.8pt);\n\\fill (0:x3) circle (0.8pt) node[above] {$x_2$};\n\\end{tikzpicture}"
          }
        ],
      },
    ],
  },
  {
    id: "physics",
    name: "Vật lý",
    subCategories: [
      {
        name: "Cơ học",
        templates: [
          {
            id: "inclined-plane",
            title: "Mặt phẳng nghiêng",
            description:
              "Vật trượt trên mặt phẳng nghiêng với các lực tác dụng.",
            code: `\\begin{tikzpicture}
  \\draw (0,0) -- (4,0) -- (4,2) -- cycle;
  \\draw (2.5, 1.25) -- ++(30:1) -- ++(120:1) -- ++(210:1) -- cycle;
  \\draw[->] (3, 1.75) -- ++(0,-1.5) node[below] {$P$};
  \\draw[->] (3, 1.75) -- ++(120:1) node[above] {$N$};
\\end{tikzpicture}`,
          },
          {
            id: "pendulum",
            title: "Con lắc đơn",
            description: "Mô hình con lắc đơn dao động.",
            code: `\\begin{tikzpicture}
  \\draw[dashed] (0,0) -- (0,-3);
  \\draw (0,0) -- (-1,-2.8);
  \\fill [blue] (-1,-2.8) circle (0.2);
  \\draw (-1,-2.8) -- (-1,-3.8) node[below] {$P$};
  \\draw[->] (-1,-2.8) -- (-0.5, -2.6) node[right] {$T$};
  \\draw (0,-0.5) arc (270:250:0.5);
  \\node at (-0.2,-0.7) {$\\theta$};
  \\fill (0,0) circle (0.4pt);
  \\draw (-0.5,0) -- (0.5,0);
\\end{tikzpicture}`,
          },
        ],
      },
      {
        name: "Điện học",
        templates: [
          {
            id: "circuit",
            title: "Mạch điện cơ bản",
            description: "Mạch gồm nguồn, điện trở và tụ điện.",
            code: `\\begin{tikzpicture}
  \\draw (0,0) to[battery1] (0,3)
    to[R=$R_1$] (3,3)
    to[C=$C_1$] (3,0) -- (0,0);
\\end{tikzpicture}`,
          },
          {
            id: "machdien-rc-h13",
            title: `Mạch điện RC nối tiếp (H13)`,
            description: `Mạch điện RC nối tiếp (vật lý)`,
            code: String.raw`\begin{tikzpicture}[every node/.style={font=\normalsize}]
 \draw (0,0) to[battery1] (0,3) to[R=$R_1$] (3,3) to[C=$C_1$] (3,0) -- (0,0);
\end{tikzpicture}`,
          },
        ],
      },
    ],
  },
  {
    id: "chemistry",
    name: "Hóa học",
    subCategories: [
      {
        name: "Cấu trúc phân tử",
        templates: [
          {
            id: "benzene",
            title: "Vòng Benzen",
            description: "Cấu trúc phân tử Benzen.",
            code: `\\begin{tikzpicture}
  \\draw (0,0) -- (1,0.5) -- (1,1.5) -- (0,2) -- (-1,1.5) -- (-1,0.5) -- cycle;
  \\draw (0,0.5) circle (0.5);
\\end{tikzpicture}`,
          },
          {
            id: "ethanol",
            title: "Ethanol",
            description: "Công thức cấu tạo của Ethanol.",
            code: `\\begin{tikzpicture}
    \\node (C') at (0,0) {C};
    \\node (C2) at (1.5,0) {C};
    \\node (O) at (3,0) {O};
    \\node (H) at (3.8,0.5) {H};
    
    \\draw (C') -- (C2) -- (O) -- (H);
    % Add hydrogens
    \\node at (0,1) {H}; \\draw (C') -- (0,0.7);
    \\node at (0,-1) {H}; \\draw (C') -- (0,-0.7);
    \\node at (-1,0) {H}; \\draw (C') -- (-0.7,0);
    \\node at (1.5,1) {H}; \\draw (C2) -- (1.5,0.7);
    \\node at (1.5,-1) {H}; \\draw (C2) -- (1.5,-0.7);
\\end{tikzpicture}`,
          },
          {
            id: "metan-ch4-h15",
            title: `Công thức Metan (H15)`,
            description: `Công thức hóa học (metan CH4)`,
            code: String.raw`\begin{tikzpicture}[every node/.style={font=\normalsize}]
 \node (C') at (0,0) {C};
 \node (C2) at (1.5,0) {C};
 \node (O) at (3,0) {O};
 \node (H) at (3.8,0.5) {H};
 \draw (C') -- (C2) -- (O) -- (H);
 \node at (0,1) {H}; \draw (C') -- (0,0.7);
 \node at (0,-1) {H}; \draw (C') -- (0,-0.7);
 \node at (-1,0) {H}; \draw (C') -- (-0.7,0);
 \node at (1.5,1) {H}; \draw (C2) -- (1.5,0.7);
 \node at (1.5,-1) {H}; \draw (C2) -- (1.5,-0.7);
\end{tikzpicture}`,
          },
        ],
      },
      {
        name: "Dụng cụ thí nghiệm",
        templates: [
          {
            id: "beaker",
            title: "Cốc thí nghiệm",
            description: "Cốc chứa dung dịch.",
            code: `\\begin{tikzpicture}
  \\draw[thick] (-1,2) -- (-1,0) arc (180:360:1 and 0.2) -- (1,2);
  \\draw (-1,2) ellipse (1 and 0.2);
  \\fill[cyan!30] (-1,0.5) -- (-1,0) arc (180:360:1 and 0.2) -- (1,0.5) -- cycle;
  \\draw[dashed] (0,0) ellipse (1 and 0.2);
\\end{tikzpicture}`,
          },
        ],
      },
    ],
  },
  {
    id: "real-world",
    name: "Hình vẽ thực tế (PDF)",
    subCategories: [
      {
        name: "Đồ vật & Thiết bị",
        templates: [
          {
            id: "rw-clock",
            title: "1. Đồng hồ",
            description: "Vẽ đồng hồ kim.",
            code: `\\begin{tikzpicture}[scale=0.6,transform shape]
\\begin{scope}
\\shade[draw,left color=white, right color=white!80!gray] (0,0) circle (3.1);
\\def \\R{3}
\\foreach \\i in {0,...,60}{
\\draw[black!50!,line width=1.2pt]
(\\i*6:\\R-0.15) -- (\\i*6:\\R);
}
\\foreach \\i in {1,2,...,12}{
\\draw[line width=2pt]
(90-\\i*30:\\R)--(90-\\i*30:\\R-0.3) node[shift=(90-\\i*30:-0.4)]{\\LARGE \\i} ;
}
%%Kim đồng hồ
\\fill (10:0.35)--(-10:0.35)--(-179:1.5)--(179:1.5)
(-80:0.4)--(-100:0.4)--(91:1.7)--(89:1.7)
;
\\def\\goc{210}
\\begin{scope}[rotate=\\goc]
\\fill[red] (-93:0.75) rectangle (-81:0.3);
\\draw[red] (-90:0.4)--(90:1.7);
\\end{scope}
\\fill[red] (0,0) circle (0.4pt);
\\end{scope}
\\end{tikzpicture}`,
          },
          {
            id: "rw-cylinder-joint",
            title: "2. Khớp nối hai nửa hình trụ",
            description: "Hình học không gian: giao tuyến trụ.",
            code: `\\begin{tikzpicture}[semithick]
\\draw[dashed] (-3.73,-2.22) coordinate (A) -- (0,0) coordinate (B) -- (4.29,-2.06) coordinate 
(C);
\\path ($(A)+(0,1.94)$) coordinate (E) --(0,1.94) coordinate (D)--($(C)+(0,1.94)$) coordinate 
(F);
\\draw
(-81:1.63) coordinate (O) -- (-2.1,-3.01) coordinate (H) -- (A)
-- (E) -- (D) -- (F) -- (C) -- (2.88,-2.88) coordinate (G)-- cycle
(E) .. controls +(-30:1.84) and +(95:0.88) .. (H)
(G) .. controls +(104:1.12) and +(-158:1.04) .. (F)
(D).. controls +(-60:1.36) and +(75:1.36) ..(O);
\\draw[dashed] (D).. controls +(-138:0.88) and +(89:1.44) .. ($(B)!0.35!(A)$) coordinate 
--(O)--($(B)!0.38!(C)$) coordinate (M).. controls +(86:1.2) and +(-28:1.28) .. (D)
(O)--(B)--(D);
\\foreach \\t/\\g in {A/-90, B/50, C/-90, E/90, D/90, F/90, O/-90, H/-90, G/-90, N/135, M/30}{
\\fill (\\t) circle (0.4pt) node[shift={(\\goc:9pt)}]{$\\t$};
}
\\end{tikzpicture}`,
          },
          {
            id: "rw-bicycle",
            title: "3. Xe đạp",
            description: "Vẽ xe đạp dùng lệnh \\pic.",
            code: `\\begin{tikzpicture}[scale=.8,transform shape]
\\fill[black] 
(2.54,2.82).. controls +(130:0.06) and ++(120:0.08)..(2.54,2.73)--(2.87,2.79)--
(2.85,2.88) --cycle
(2.57,2.5).. controls +(130:0.06) and ++(120:0.08)..(2.57,2.41)--(2.9,2.47)--
(2.88,2.56)--cycle
;
\\draw[black,line width=1] (2.94,2.69)--(3.04,2.4);
\\draw[gray, line width=1] 
(2.87,2.84).. controls +(0:0.2) and ++(30:0.2).. (2.94,2.69).. controls +(-10:0.1) 
and ++(30:0.2).. (2.9,2.52)
;
\\draw[gray!50!white, line width=1.75] (3.02,2.34)--(3.08,2.36)
(1.18,2.27)--(1.16,2.34);
\\draw[gray,line width=0.75] (1.54,2.53).. controls +(-70:0.1) and ++(20:0.3).. 
(1.15,2.38)--(0.91,2.32)
;
\\draw[gray,line width=0.75,decoration={aspect=0.3, segment length=0.4mm, 
amplitude=0.3mm,coil},decorate] (0.91,2.32)--(0.91,2.55);
\\fill[left color=brown!80!white,right color=brown] (1.66,2.56)--(1.58,2.61).. 
controls +(150:0.1) and ++(-10:0.4).. (0.87,2.66).. controls +(-180:0.08) and ++(150:0.08).. 
(0.86,2.57).. controls +(-30:0.1) and ++(140:0.2).. (1.19,2.42)--(1.22,2.42)--cycle
;
%%van
\\tikzset{van/.pic={ 
\\draw[gray,line width=1] (0.1,-0.1)--(0.1,0.2);
\\fill [black!40!gray] (0,0.1)--(0,0.3).. controls +(60:0.1) and 
++(120:0.1)..(0.2,0.3)--(0.2,0.1)--cycle;
}}
\\path 
(3,0)pic[scale=0.3,shift=(60:0.25),rotate=-45]{van}
(-1,0)pic[scale=0.3,shift=(50:1.75),rotate=-70]{van}
;
%%bánh xe
\\path 
(.28, .75) coordinate (I)
(3.78, .75) coordinate (J)
(1.84, .51) coordinate (K)
;
\\def\\R{1.1}
\\foreach \\n/\\m in {I/7,J/0}{
\\begin{scope}[shift={(\\n)},scale=1]
\\foreach \\i in {1,2,...,12}{
\\pgfmathsetmacro{\\goc}{\\i*360/12+\\m}
\\draw[gray!90!black] (0,0) -- ($(0,0)+(\\goc:\\R)$);
}
\\end{scope}
\\draw[line width=1.5] (\\n) circle (\\R);
\\draw[white!70!gray,line width=1] (\\n) circle (\\R-.05);
}
\\draw[line width=0.5] (I)--(-.65,1.35) (J)--(2.7,.69);
\\fill [red] (-0.78,1.5).. controls +(90:0.08) and ++(150:0.1).. (-0.63,1.5)--cycle;
\\fill [white!70!gray] 
(-0.78,1.22).. controls +(100:0.1) and ++(-180:0.04).. (-0.8,1.5)--(-0.58,1.51)--
cycle;
%%cái dè
\\fill[gray!70!black]
(2.7,0.3).. controls +(105:1.1) and ++(175:0.7).. (3.93,1.9).. controls +(-
60:0.06) and ++(60:0.04)..(3.92,1.8).. controls +(180:0.7) and ++(90:0.5).. (2.76,.69).. 
controls +(-70:0.2) and ++(50:0.2).. cycle
(-0.87,0.95).. controls +(75:1.4) and ++(96:1.3).. (1.42,0.85)--(1.29,0.86).. 
controls +(100:1.36) and ++(75:1).. (-0.76,0.98)--cycle
;
%%sườn xe
\\draw[line width=1] (1.18,2.15)--(.39,.9)
(.97,1.86)--(.71,2)--(-.23,2).. controls +(180:.1) and ++(90:.1).. (-.37,1.83)--
(.21,.9)
;
\\draw[line width=1.75] (1.24,2.23)--(3.09,2.23)--(3.07,2.29)
(3.09,2.24)--(3.23,1.84)
(2.04,.77)--(3.1,1.91)--(3.2,1.91)--(3.47,1.15)
;
\\fill[black] (3.43,1.16).. controls +(-80:.21) and ++(150:0).. (3.75, .75)--(3.79, 
.76).. controls +(150:.2) and ++(-70:.02)..(3.5,1.17)--cycle ;
\\draw[line width=2,line cap=butt] (1.18,2.27)--(1.73,.78);
%%chắn xích
\\fill[gray!90!]
(.18,.56).. controls +(140:0.25) and ++(-170:0.15).. (.24,.91)--
(1.88,.84).. controls +(-6:0.4) and ++(-4.5:0.5).. (1.79,.18)--cycle
;
\\fill[white!80!gray] 
(.71,.58).. controls +(150:0.17) and ++(-180:0.1).. (.76,.75)--(1.4,.7).. controls 
+(-20:0.05) and ++(90:0.1)..(1.5,0.57).. controls +(-100:0.1) and ++(-6:0.05).. (1.37,.45)--
cycle
;
\\fill (I) circle (.05) (J) circle (.05);
\\draw[white] (K) circle (.3);
\\fill[white] (K) circle (0.15);
%%bàn đạp
\\draw[line width=1] (K)--(1.75,0.79) (1.96,0.2)--(2,0.1);
\\tikzset{bandap/.pic={
\\fill[gray] (0,0) rectangle ++(2.5,1);
\\fill[gray] (.2,0).. controls +(-60:.08) and ++(180:.08).. (.5,-.3)--
(2,-.3).. controls +(40:.1) and ++(-90:.08).. (2.3,0)--cycle;
\\fill[gray](.4,0).. controls +(-60:.08) and ++(180:.08).. (.65,-.2)--
(1.75,-.2).. controls +(40:.1) and ++(-90:.08).. (2,0)--cycle;
}}
\\path
(2,0)pic[scale=.1,shift=(117:8.2),rotate=-20]{bandap}
(2,0)pic[scale=.1,shift=(-180:0.9),rotate=-15]{bandap}
;
\\end{tikzpicture}`,
          },
          {
            id: "matdongho-h17",
            title: `Mặt đồng hồ (H17)`,
            description: `Mặt đồng hồ (kim đồng hồ)`,
            code: String.raw`\begin{tikzpicture}[scale=0.6, transform shape, every node/.style={font=\normalsize}]
 \begin{scope}
 \shade[draw, left color=white, right color=white!80!gray] (0,0) circle (3.1);
 \def \R{3}
 \foreach \i in {0,...,60}{
 \draw[black!50!, line width=1.2pt] (\i*6:\R-0.15) -- (\i*6:\R);
 }
 \foreach \i in {1,2,...,12}{
 \draw[line width=2pt] (90-\i*30:\R)--(90-\i*30:\R-0.3) node[shift=(90-\i*30:-0.4)]{\LARGE \i};
 }
 \fill (10:0.35)--(-10:0.35)--(-179:1.5)--(179:1.5) (-80:0.4)--(-100:0.4)--(91:1.7)--(89:1.7);
 \def\goc{210}
 \begin{scope}[rotate=\goc]
 \fill[red] (-93:0.75) rectangle (-81:0.3);
 \draw[red] (-90:0.4)--(90:1.7);
 \end{scope}
 \fill[red] (0,0) circle (3pt);
 \end{scope}
\end{tikzpicture}`,
          },
        ],
      },
      {
        name: "Phương tiện (Xe, Máy bay)",
        templates: [
          {
            id: "rw-plane-1",
            title: "4. Máy bay 1 (Đổi màu)",
            description: "Vẽ máy bay với cánh, thân.",
            code: `\\begin{tikzpicture}[line width =2pt]
\\def\\canh{
\\path[draw] (-4.32, 7.47) -- (-6.91, 7.48 ) -- (-8.6, 8.23) .. controls +(155:0.17) and 
+(168:0.17) ..
(-8.5, 8.53) -- (-5.61, 7.69) -- (-2.68, 8.56) .. controls +(12:0.23) and +(28:0.23) ..
(-2.58, 8.27) -- cycle;
\\path[draw, fill=white] (-5.93, 6.57) -- (-5.87, 7.77) .. controls +(86:0.29) and +(94:0.23) ..
(-5.31, 7.78 ) -- (-5.26, 6.55);
\\path[draw, rounded corners] (-6.25, 4.01) -- (-5.9, 2.88 ) -- (-5.33, 2.88 ) -- (-5.01, 4.08 ) ;
\\path[draw, fill=white] (-6.21, 3.88 ) .. controls +(177:0.12) and +(-88:0.17) ..
(-6.4, 4.24) .. controls +(92:0.7) and +(-89:0.58 ) ..
(-6.45, 6.32) .. controls +(92:0.17) and +(180:0.17) ..
(-6.06, 6.74) .. controls +(0:0.29) and +(179:0.29) ..
(-5.15, 6.73) .. controls +(-1:0.23) and +(90:0.23) ..
(-4.71, 6.35) .. controls +(-90:0.75) and +(0:0) ..
(-4.75, 4.27) -- (-4.93, 3.87) .. controls +(-179:0.46) and +(-1:0.46) ..
(-6.21, 3.88 ) -- cycle
}
\\canh;
\\begin{scope}[xscale=-1]
\\canh;
\\end{scope}
\\def\\chan{(-2.63, 3.65) .. controls +(-128:1.74) and +(70:1.45) ..
(-4.94, -1.23) .. controls +(-110:0.23) and +(-119:0.23) ..
(-4.58, -1.44) .. controls +(62:0.81) and +(-141:2.09) ..
(-1.67, 2.94) .. controls +(177:0.46) and +(-78:0.52) ..
(-2.63, 3.65) -- cycle
}
\\path[draw]\\chan;
\\path[draw, xscale=-1]\\chan;
%Thân trong
\\path[draw] (-0.41, 6.46) .. controls +(0:0) and +(-92:0.17) ..
(-0.41, 6.96) .. controls +(90:0.12) and +(-177:0.12) ..
(-0.23, 7.14) .. controls +(5:0.12) and +(176:0.17) ..
(0.2, 7.14) .. controls +(-3:0.12) and +(90:0.12) ..
(0.39, 6.98 ) .. controls +(-88:0.17) and +(0:0) ..
(0.39, 6.46);
\\path[draw] (-0.66, 2.78 ) -- (-0.66, 1.8 ) (0.67, 2.85) -- (0.67, 1.73);
\\path[draw, fill=white] (-0.97, 1.94) -- (0.97, 1.94) -- (0.98, 0.42) .. controls +(-88:0.17) and 
+(-3:0.23) ..
(0.56, 0.1) -- (-0.6, 0.1) .. controls +(-175:0.17) and +(-91:0.23) ..
(-0.97, 0.42) -- cycle;
\\path[draw, fill=white] (1.18, 2.58 ) .. controls +(-180:0.7) and +(-0:0.75) ..
(-1.17, 2.58 ) .. controls +(179:0.41) and +(-93:0.29) ..
(-1.73, 3.3) .. controls +(87:0.87) and +(-104:0.75) ..
(-1.48, 5.95) .. controls +(76:0.52) and +(180:1.04) ..
(0, 6.64) .. controls +(0:1.04) and +(106:0.41) ..
(1.43, 5.97) .. controls +(-73:0.41) and +(94:0.87) ..
(1.81, 3.34) .. controls +(-86:0.29) and +(0:0.41) ..
(1.18, 2.58 ) -- cycle;
%Mình
\\path[draw, fill=white] (-1.5, 6) -- (-4, 5.5) .. controls +(0:0) and +(-1:0.75) ..
(-6.4, 5.5) .. controls +(180:0.17) and +(88:0.12) ..
(-6.7, 5.3) .. controls +(-94:0.29) and +(92:0.29) ..
(-6.7, 4.5) .. controls +(-88:0.12) and +(180:0.12) ..
(-6.4, 4.25) .. controls +(-1:0.64) and +(0:0) ..
(-4.3, 4.25) -- (-1.8, 3.3) -- (1.8, 3.3) -- (4.3, 4.25) .. controls +(0:0) and +(180:0.64) ..
(6.4, 4.25) .. controls +(0:0.23) and +(-92:0.17) ..
(6.7, 4.5) .. controls +(88:0.23) and +(-91:0.29) ..
(6.7, 5.3) .. controls +(90:0.12) and +(0:0.12) ..
(6.4, 5.5) .. controls +(-179:0.7) and +(0:0) ..
(4, 5.5) -- (1.5, 6) -- cycle;
\\path[draw] (0, 0.99) circle (0.58 ) ;
\\draw (-3.19, 4.84) circle (0.4)
(-1.45, 4.84) circle (0.4)
(1.45, 4.84) circle (0.4)
(3.19, 4.84) circle (0.4);
\\end{tikzpicture}`,
          },
          {
            id: "rw-plane-2",
            title: "5. Máy bay 2 (màu trắng)",
            description: "Vẽ máy bay nét đậm.",
            code: `\\begin{tikzpicture}[thick]
%đuôi phải
\\draw (4.83,7.13) .. controls +(0:0) and +(-162:0.3) ..
(5.83,7.48 ) .. controls +(24:0.1) and +(170:0.1) ..
(6.16,7.5) .. controls +(-10:0.3) and +(169:0.3) ..
(7.17,7.31) .. controls +(-10:0.1) and +(36:0.1) ..
(7.2,7.17) .. controls +(-144:0.3) and +(0:0) ..
(5.97,6.31)
(5.01,6.89) .. controls +(0:0) and +(-156:0.2) ..
(6.13,7.31) .. controls +(18:0) and +(-18:0) ..
(6.12,7.37) .. controls +(171:0.1) and +(0:0) ..
(5.72,7.44);
%Cánh trái
\\draw (10.15,5.45) .. controls +(0:0) and +(-157:0.4) ..
(14.3,7.28 ) .. controls +(18:0) and +(-90:0) ..
(14.36,7.36) .. controls +(90:0) and +(-95:0.1) ..
(14.37,7.76) .. controls +(90:0.1) and +(173:0.1) ..
(14.49,7.88 ) .. controls +(-4:0.3) and +(173:0.3) ..
(15.61,7.74) .. controls +(-11:0.2) and +(105:0.1) ..
(15.83,7.56) .. controls +(-75:0.2) and +(106:0.1) ..
(15.97,7.09) .. controls +(-73:0.1) and +(39:0.1) ..
(15.89,6.83) .. controls +(-136:0.6) and +(0:0) ..
(13.62,4.72)
(13.07,4.86) -- (15.79,7.03) -- (15.74,7.11) -- (14.49,7.29)
(13.84,7.07) .. controls +(0:0) and +(174:0.2) ..
(14.43,7) .. controls +(-7:0.1) and +(27:0.1) ..
(14.45,6.9) .. controls +(-156:0.2) and +(23:0.4) ..
(13.38,6.42) .. controls +(-158:0.1) and +(-10:0.1) ..
(13.22,6.39) .. controls +(170:0.2) and +(0:0) ..
(12.57,6.51) (12.07,6.29) .. controls +(0:0) and +(170:0.1) ..
(12.63,6.2) .. controls +(-11:0.1) and +(29:0.1) ..
(12.63,6.09) .. controls +(-152:0.4) and +(0:0) ..
(10.9,5.3);
\\def\\than{
(6.15,3.69) .. controls +(158:0.7) and +(-41:1) ..
(2.33,6.49) .. controls +(140:0.3) and +(-173:0.3) ..
(2.43,7) .. controls +(0:0.1) and +(170:0.1) ..
(2.8,6.96) .. controls +(-10:2.7) and +(168:3.2) ..
(14.21,4.59) .. controls +(-12:1) and +(125:0.9) ..
(16.68,3.02) .. controls +(-32:0.4) and +(73:0.3) ..
(17.52,1.88 ) .. controls +(-106:0.7) and +(-3:1) ..
(14.58,1.13) .. controls +(177:1.9) and +(-22:2.2) ..
(6.15,3.69) -- cycle
}
\\draw[fill=white] \\than;
%Cánh trên
\\draw[fill=white](3.04,6.66) .. controls +(-17:0.1) and +(-97:0.2) ..
(5.38,6.29) .. controls +(83:0.2) and +(-54:0.9) ..
(3.12,9.47) .. controls +(126:0.1) and +(-6:0.1) ..
(2.89,9.62) .. controls +(168:0.2) and +(63:0.1) ..
(1.78,9.69) .. controls +(-119:0.1) and +(111:1) ..
(2.85,6.84) .. controls +(-67:0.1) and +(162:0.1) ..
(3.04,6.66) -- cycle;
\\draw (1.91,9.22) .. controls +(0:0) and +(170:0.1) ..
(2.33,9.17) .. controls +(0:0) and +(117:0) ..
(2.37,9.13) .. controls +(-66:0.1) and +(111:0.2) ..
(3.2,7.01) .. controls +(-63:0) and +(-27:0) ..
(3.17,6.97) .. controls +(180:0) and +(-12:0.1) ..
(2.79,7.01);
\\draw[fill=white](2.81,6.32) .. controls +(-13:0.5) and +(165:0.5) ..
(4.52,5.91) .. controls +(-14:0.2) and +(11:0.2) ..
(4.58,5.62) .. controls +(-168:0.7) and +(10:0.6) ..
(2.13,5.14) .. controls +(-168:0.1) and +(-12:0.1) ..
(1.58,5.12) .. controls +(164:0.3) and +(-17:0.3) ..
(0.46,5.44) .. controls +(164:0.1) and +(-157:0.1) ..
(0.46,5.54) .. controls +(20:0.5) and +(-160:0.6) ..
(2.57,6.31) .. controls +(21:0.1) and +(166:0.1) ..
(2.81,6.32) -- cycle;
\\draw (2.44,6.26) .. controls +(0:0) and +(165:0.1) ..
(2.82,6.16) .. controls +(-11:0.1) and +(14:0) ..
(2.83,6.09) .. controls +(-160:0.3) and +(20:0.3) ..
(1.29,5.53) .. controls +(-160:0.1) and +(-16:0.1) ..
(1.08,5.5) .. controls +(162:0.1) and +(0:0) ..
(0.68,5.62);
%Óng tống
\\draw (8.89,0.07) .. controls +(174:0.4) and +(-32:0.4) ..
(7.25,0.61) .. controls +(148:0.4) and +(-103:0.6) ..
(6.8,1.62);
\\draw (9.19,1.54) .. controls +(148:0.4) and +(-21:0.4) ..
(8.11,1.98);
\\draw[fill=white](8.33,0.97) .. controls +(83:0.3) and +(162:0.3) ..
(9.19,1.54) .. controls +(-18:0.5) and +(75:0.3) ..
(9.6,0.58 ) .. controls +(-105:0.3) and +(-18:0.3) ..
(8.85,0.07) .. controls +(162:0.6) and +(-96:0.4) ..
(8.33,0.97) -- cycle;
\\draw (8.51,0.92) .. controls +(79:0.3) and +(169:0.3) ..
(9.14,1.39) .. controls +(-12:0.4) and +(74:0.4) ..
(9.47,0.6) .. controls +(-105:0.2) and +(-4:0.3) ..
(8.9,0.2) .. controls +(177:0.3) and +(-100:0.4) ..
(8.51,0.92) -- cycle;
\\draw[fill=white] (8.3,2.03) .. controls +(0:0) and +(56:0.1) ..
(8.43,1.73) .. controls +(-128:0.2) and +(0:0) ..
(7.76,1.88);
\\draw (8.7,1.23) .. controls +(-24:0.2) and +(72:0.2) ..
(8.94,0.83) .. controls +(-108:0.2) and +(-13:0.3) ..
(8.5,0.64)
(8.96,1.38 ) .. controls +(-31:0.2) and +(77:0.2) ..
(9.17,0.79) .. controls +(-103:0.3) and +(-4:0.3) ..
(8.61,0.36);
%Cánh trái
\\draw[fill=white](1.93,0.57) -- (1.49,1.16) --
(1.39,1.25) .. controls +(0:0) and +(-25:0.3) ..
(0.17,1.82) .. controls +(157:0.1) and +(97:0.1) ..
(0.04,1.71) .. controls +(-79:0.2) and +(114:0.1) ..
(0.17,1.27) .. controls +(-68:0.1) and +(150:0.1) ..
(0.34,1.09) .. controls +(-27:0.3) and +(161:0.5) ..
(1.87,0.42) .. controls +(-16:0.1) and +(-163:0.1) ..
(2.25,0.4) .. controls +(14:1.4) and +(-164:1) ..
(9.97,2.49) .. controls +(15:0.4) and +(-19:0.4) ..
(9.96,2.93) .. controls +(162:0.8 ) and +(-14:0.8 ) ..
(6.87,3.79) .. controls +(166:0.2) and +(24:0.2) ..
(6.36,3.78 ) .. controls +(-157:1.5) and +(0:0) ..
(1.01,1.43);
\\draw (1.89,0.63) -- (9.67,2.99)
(1.12,1.48 ) .. controls +(0:0) and +(156:0.1) ..
(1.66,1.23) .. controls +(-18:0.1) and +(-162:0.1) ..
(1.85,1.23) .. controls +(24:0.2) and +(-155:0.3) ..
(3.26,1.85) .. controls +(23:0.1) and +(-27:0.1) ..
(3.25,1.97) .. controls +(161:0.2) and +(0:0) ..
(2.71,2.18)
(3.26,2.42) .. controls +(0:0) and +(162:0.2) ..
(3.79,2.21) .. controls +(-18:0.1) and +(-157:0.1) ..
(4.01,2.2) .. controls +(23:0.5) and +(-155:0.4) ..
(6.51,3.32) .. controls +(23:0.1) and +(-18:0.1) ..
(6.52,3.44) .. controls +(163:0.2) and +(0:0) ..
(5.97,3.61)
(4.7,4.63) -- (13.75,2.22) .. controls +(-11:1.6) and +(-112:0.7) ..
(16.9,2.86);
\\draw[fill=white](13.67,2.81) .. controls +(-102:0.2) and +(100:0.2) ..
(13.65,1.84) .. controls +(-82:0.1) and +(-4:0.1) ..
(13.53,1.69) -- (12.98,1.82) .. controls +(163:0.1) and +(-84:0.1) ..
(12.79,2.02) .. controls +(99:0.3) and +(-111:0.3) ..
(12.86,3.04) .. controls +(68:0.1) and +(174:0.1) ..
(13.02,3.1) -- (13.56,2.97) .. controls +(-23:0.1) and +(78:0.1) ..
(13.67,2.81) -- cycle;
\\draw (17.19,2.58 ) .. controls +(-146:0.4) and +(103:0.6) ..
(16.83,1.34)
(16.68,3.02) .. controls +(-125:0.7) and +(-2:0.5) ..
(15.01,2.41) .. controls +(178:0.5) and +(-174:0.4) ..
(14.95,3.01) .. controls +(6:0.5) and +(-133:0.6) ..
(16.32,3.45)
(15.47,3.06) -- (15.62,2.43) -- (15.63,2.44)
(16.1,3.27) -- (16.48,2.79);
\\foreach \\x/\\y in {7.42/4.28,8.14/4.1,8.83/3.92,9.58/3.73,10.33/3.53,11.93/3.12,11.1/3.33}
\\draw (\\x,\\y) ellipse (0.15 and 0.16);
\\end{tikzpicture}`,
          },
          {
            id: "rw-plane-3",
            title: "6. Máy bay 3 (màu trắng)",
            description: "Vẽ máy bay với shading và clip.",
            code: `\\begin{tikzpicture}[line width=3pt]
\\def\\thanmaybay{(15.5,0.29).. controls (15.5,0.29) and (17.72,0.39)..
(17.85,1.23).. controls (17.91,1.57) and (17.35,1.73)..
(17.04,1.9).. controls (16.73,2.07) and (16.38,2.34)..
(16.01,2.47).. controls (15.62,2.62) and (15.19,2.74)..
(14.77,2.75).. controls (11.33,2.84) and (0.09,2.3)..
(0.04,1.76).. controls (0.03,1.72) and (0,1.62)..
(0.03,1.58).. controls (0.4,1.03) and (3.25,0.31)..
(4.78,0.08).. controls (7.13,-0.26) and (15.5,0.29).. cycle;
}
\\path[draw,fill=cyan] (1.07,1.87) -- (0.13,4.91).. controls (0.13,4.91) and (0.63,4.99)..
(0.92,4.97).. controls (1.4,4.95) and (1.98,4.02)..
(2.72,3.29).. controls (3.23,2.78) and (3.92,2.34)..
(4.6,2.39);
\\draw[fill=white]\\thanmaybay;
\\begin{scope}
\\clip \\thanmaybay;
\\path[draw,fill=cyan!50] (16.4,2.27).. controls (16.21,2.22) and (15.97,2.19)..
(15.7,2.16).. controls (15.7,2.07) and (15.71,1.81)..
(15.75,1.5).. controls (16.25,1.62) and (16.71,1.81)..
(17.04,1.9);
\\draw (16.03,2.2) -- (16.24,1.72);
\\fill[gray!20] (-0,1.73).. controls (3.69,0.02) and (10.73,0.42)..
(17.72,1.04) -- (17.47,0.36) -- (4.78,-0.3).. controls (-0.64,0.5) and (-0.05,1.01).. (-0,1.73) --
cycle;
\\end{scope}
\\draw\\thanmaybay;
\\path[draw,fill=cyan] (2.81,1.51).. controls (2.78,1.11) and (0.89,1.26)..
(0.47,1.42).. controls (0.42,1.44) and (0.4,1.57)..
(0.4,1.57).. controls (1.54,1.69) and (2.84,1.87).. cycle;
\\path[draw,fill=gray!70] (7.49,0.65).. controls (7.73,0.43) and (8.22,0.2)..
(8.76,0.24).. controls (9.32,0.28) and (10.02,0.54)..(10.27,0.84);
\\path[draw,fill=gray] (9.3,0.31).. controls (9.02,0.29) and (8.77,0.26)..
(8.48,0.17).. controls (8.46,0.03) and (8.41,-0.18)..
(8.49,-0.27).. controls (8.66,-0.46) and (9.15,-0.42)..(9.37,-0.41);
\\path[draw,fill=gray!60] (9.22,0.32).. controls (9.09,0.24) and (9.08,-0.37)..
(9.28,-0.49).. controls (9.61,-0.7) and (10.57,-0.69)..
(11,-0.51).. controls (11,-0.51) and (11.25,0.27)..
(10.99,0.49).. controls (10.84,0.61) and (10.47,0.66)..
(10.21,0.64).. controls (9.86,0.62) and (9.45,0.48)..cycle;
\\path[draw,fill=cyan] (11.61,0.97).. controls (11.64,1.14) and (11.3,1.22)..
(11.13,1.23).. controls (9.36,1.36) and (7.01,0.95)..
(5.73,0.71).. controls (5.66,0.7) and (5.61,0.6)..
(5.66,0.56).. controls (5.75,0.48) and (6.33,0.41)..
(6.94,0.49).. controls (8.15,0.65) and (9.86,0.81)..
(10.88,0.69).. controls (11.37,0.63) and (11.59,0.82)..cycle;
\\path[shift={(10.9,0.05)},draw,fill=white,rotate=5] (0,0) ellipse (0.3 and 0.58);
\\path[draw,rounded corners] (14.31,2.22) rectangle (14.8,1.27);
\\path (5,1.45) coordinate (ta)
(12,1.5) coordinate (tb);
\\foreach \\i in {0,0.1,...,1.3}{
\\fill[rounded corners] ($(ta)!\\i!(tb)$) rectangle +(0.3,0.5);
}
\\end{tikzpicture}`,
          },
          {
            id: "banvekythuat-1-h19",
            title: `Bản vẽ kỹ thuật 1 (H19)`,
            description: `Bản vẽ kỹ thuật (mô hình phức tạp)`,
            code: String.raw`\begin{tikzpicture}[
 scale=.8,
 line join=round,
 transform shape,
 every node/.style={font=\normalsize}
]
 \fill[black] (2.54,2.82).. controls +(130:0.06) and ++(120:0.08)..(2.54,2.73)--(2.87,2.79)--(2.85,2.88) --
cycle (2.57,2.5).. controls +(130:0.06) and ++(120:0.08)..(2.57,2.41)--(2.9,2.47)--(2.88,2.56)--cycle;
 \draw[black,line width=1] (2.94,2.69)--(3.04,2.4);
 \draw[gray, line width=1] (2.87,2.84).. controls +(0:0.2) and ++(30:0.2).. (2.94,2.69).. controls +(-10:0.1) and ++(30:0.2).. (2.9,2.52);
 \draw[gray!50!white, line width=1.75] (3.02,2.34)--(3.08,2.36) (1.18,2.27)--(1.16,2.34);
 \draw[gray,line width=0.75] (1.54,2.53).. controls +(-70:0.1) and ++(20:0.3).. (1.15,2.38)--(0.91,2.32);
 \draw[gray,line width=0.75,decoration={aspect=0.3, segment length=0.4mm, 
amplitude=0.3mm,coil},decorate] (0.91,2.32)--(0.91,2.55);
 \fill[left color=brown!80!white,right color=brown] (1.66,2.56)--(1.58,2.61).. controls +(150:0.1) and 
++(-10:0.4).. (0.87,2.66).. controls +(-180:0.08) and ++(150:0.08).. (0.86,2.57).. controls +(-30:0.1) and 
++(140:0.2).. (1.19,2.42)--(1.22,2.42)--cycle;
 \tikzset{van/.pic={ 
 \draw[gray,line width=1] (0.1,-0.1)--(0.1,0.2);
 \fill [black!40!gray] (0,0.1)--(0,0.3).. controls +(60:0.1) and ++(120:0.1)..(0.2,0.3)--(0.2,0.1)--cycle;
 }}
 \path (3,0)pic[scale=0.3,shift=(60:0.25),rotate=-45]{van} (-1,0)pic[scale=0.3,shift=(50:1.75),rotate=-70]{van};
 \path (.28, .75) coordinate (I) (3.78, .75) coordinate (J) (1.84, .51) coordinate (K);
 \def\R{1.1}
 \foreach \n/\m in {I/7,J/0}{
 \begin{scope}[shift={(\n)},scale=1]
 \foreach \i in {1,2,...,12}{
 \pgfmathsetmacro{\goc}{\i*360/12+\m}
 \draw[gray!90!black] (0,0) -- ($(0,0)+(\goc:\R)$);
 }
 \end{scope}
 \draw[line width=1.5] (\n) circle (\R);
 \draw[white!70!gray,line width=1] (\n) circle (\R-.05);
 }
 \draw[line width=0.5] (I)--(-.65,1.35) (J)--(2.7,.69);
 \fill [red] (-0.78,1.5).. controls +(90:0.08) and ++(150:0.1).. (-0.63,1.5)--cycle;
 \fill [white!70!gray] (-0.78,1.22).. controls +(100:0.1) and ++(-180:0.04).. (-0.8,1.5)--(-0.58,1.51)--cycle;
 \fill[gray!70!black] (2.7,0.3).. controls +(105:1.1) and ++(175:0.7).. (3.93,1.9).. controls +(-60:0.06) and ++(60:0.04)..(3.92,1.8).. controls +(180:0.7) and ++(90:0.5).. (2.76,.69).. controls +(-70:0.2) and ++(50:0.2).. cycle (-0.87,0.95).. controls +(75:1.4) and ++(96:1.3).. (1.42,0.85)--(1.29,0.86).. controls +(100:1.36) and ++(75:1).. (-0.76,0.98)--cycle;
 \draw[line width=1] (1.18,2.15)--(.39,.9) (.97,1.86)--(.71,2)--(-.23,2).. controls +(180:.1) and ++(90:.1).. (-.37,1.83)--(.21,.9);
 \draw[line width=1.75] (1.24,2.23)--(3.09,2.23)--(3.07,2.29) (3.09,2.24)--(3.23,1.84) (2.04,.77)--(3.1,1.91)--(3.2,1.91)--(3.47,1.15);
 \fill[black] (3.43,1.16).. controls +(-80:.21) and ++(150:0).. (3.75, .75)--(3.79, .76).. controls +(150:.2) and ++(-70:.02)..(3.5,1.17)--cycle ;
 \draw[line width=2,line cap=butt] (1.18,2.27)--(1.73,.78);
 \fill[gray!90!] (.18,.56).. controls +(140:0.25) and ++(-170:0.15).. (.24,.91)--(1.88,.84).. controls +(-6:0.4) and ++(-4.5:0.5).. (1.79,.18)--cycle;
 \fill[white!80!gray] (.71,.58).. controls +(150:0.17) and ++(-180:0.1).. (.76,.75)--(1.4,.7).. controls +(-20:0.05) and ++(90:0.1)..(1.5,0.57).. controls +(-100:0.1) and ++(-6:0.05).. (1.37,.45)--cycle;
 \fill (I) circle (.05) (J) circle (.05);
 \draw[white] (K) circle (.3);
 \fill[white] (K) circle (0.15);
 \draw[line width=1] (K)--(1.75,0.79) (1.96,0.2)--(2,0.1);
 \tikzset{bandap/.pic={
 \fill[gray] (0,0) rectangle ++(2.5,1);
 \fill[gray] (.2,0).. controls +(-60:.08) and ++(180:.08).. (.5,-.3)--(2,-.3).. controls +(40:.1) and ++(-90:.08).. (2.3,0)--cycle;
 \fill[gray](.4,0).. controls +(-60:.08) and ++(180:.08).. (.65,-.2)--(1.75,-.2).. controls +(40:.1) and ++(-90:.08).. (2,0)--cycle;
 }}
 \path (2,0)pic[scale=.1,shift=(117:8.2),rotate=-20]{bandap} (2,0)pic[scale=.1,shift=(-180:0.9),rotate=-15]{bandap};
\end{tikzpicture}`,
          },
          {
            id: "banvekythuat-2-h20",
            title: `Bản vẽ kỹ thuật 2 (H20)`,
            description: `Bản vẽ kỹ thuật (đối xứng, phức tạp)`,
            code: String.raw`\begin{tikzpicture}[
 line join=round,
 line width =2pt,
 every node/.style={font=\normalsize}
]
 \def\canh{
 \path[draw] (-4.32, 7.47) -- (-6.91, 7.48 ) -- (-8.6, 8.23) .. controls +(155:0.17) and +(168:0.17) .. (-8.5, 8.53) -- (-5.61, 7.69) -- (-2.68, 8.56) .. controls +(12:0.23) and +(28:0.23) .. (-2.58, 8.27) -- cycle;
 \path[draw, fill=white] (-5.93, 6.57) -- (-5.87, 7.77) .. controls +(86:0.29) and +(94:0.23) .. (-5.31, 7.78) -- (-5.26, 6.55);
 \path[draw, rounded corners] (-6.25, 4.01) -- (-5.9, 2.88 ) -- (-5.33, 2.88 ) -- (-5.01, 4.08 ) ;
 \path[draw, fill=white] (-6.21, 3.88 ) .. controls +(177:0.12) and +(-88:0.17) .. (-6.4, 4.24) .. controls +(92:0.7) and +(-89:0.58 ) .. (-6.45, 6.32) .. controls +(92:0.17) and +(180:0.17) .. (-6.06, 6.74) .. controls +(0:0.29) and +(179:0.29) .. (-5.15, 6.73) .. controls +(-1:0.23) and +(90:0.23) .. (-4.71, 6.35) .. controls +(-90:0.75) and +(0:0) .. (-4.75, 4.27) -- (-4.93, 3.87) .. controls +(-179:0.46) and +(-1:0.46) .. (-6.21, 3.88) -- cycle;
 }
 \canh;
 \begin{scope}[xscale=-1]
 \canh;
 \end{scope}
 \def\chan{(-2.63, 3.65) .. controls +(-128:1.74) and +(70:1.45) .. (-4.94, -1.23) .. controls +(-110:0.23) and +(-119:0.23) .. (-4.58, -1.44) .. controls +(62:0.81) and +(-141:2.09) .. (-1.67, 2.94) .. controls +(177:0.46) and +(-78:0.52) .. (-2.63, 3.65) -- cycle}
 \path[draw]\chan;
 \path[draw, xscale=-1]\chan;
 \path[draw] (-0.41, 6.46) .. controls +(0:0) and +(-92:0.17) .. (-0.41, 6.96) .. controls +(90:0.12) and +(-177:0.12) .. (-0.23, 7.14) .. controls +(5:0.12) and +(176:0.17) .. (0.2, 7.14) .. controls +(-3:0.12) and +(90:0.12) .. (0.39, 6.98 ) .. controls +(-88:0.17) and +(0:0) .. (0.39, 6.46);
 \path[draw] (-0.66, 2.78 ) -- (-0.66, 1.8 ) (0.67, 2.85) -- (0.67, 1.73);
 \path[draw, fill=white] (-0.97, 1.94) -- (0.97, 1.94) -- (0.98, 0.42) .. controls +(-88:0.17) and +(-3:0.23) .. (0.56, 0.1) -- (-0.6, 0.1) .. controls +(-175:0.17) and +(-91:0.23) .. (-0.97, 0.42) -- cycle;
 \path[draw, fill=white] (1.18, 2.58 ) .. controls +(-180:0.7) and +(-0:0.75) .. (-1.17, 2.58 ) .. controls +(179:0.41) and +(-93:0.29) .. (-1.73, 3.3) .. controls +(87:0.87) and +(-104:0.75) .. (-1.48, 5.95) .. controls +(76:0.52) and +(180:1.04) .. (0, 6.64) .. controls +(0:1.04) and +(106:0.41) .. (1.43, 5.97) .. controls +(-73:0.41) and +(94:0.87) .. (1.81, 3.34) .. controls +(-86:0.29) and +(0:0.41) .. (1.18, 2.58 ) -- cycle;
 \path[draw, fill=white] (-1.5, 6) -- (-4, 5.5) .. controls +(0:0) and +(-1:0.75) .. (-6.4, 5.5) .. controls +(180:0.17) and +(88:0.12) .. (-6.7, 5.3) .. controls +(-94:0.29) and +(92:0.29) .. (-6.7, 4.5) .. controls +(-88:0.12) and +(180:0.12) .. (-6.4, 4.25) .. controls +(-1:0.64) and +(0:0) .. (-4.3, 4.25) -- (-1.8, 3.3) -- (1.8, 3.3) -- (4.3, 4.25) .. controls +(0:0) and +(180:0.64) .. (6.4, 4.25) .. controls +(0:0.23) and +(-92:0.17) .. (6.7, 4.5) .. controls +(88:0.23) and +(-91:0.29) .. (6.7, 5.3) .. controls +(90:0.12) and +(0:0.12) .. (6.4, 5.5) .. controls +(-179:0.7) and +(0:0) .. (4, 5.5) -- (1.5, 6) -- cycle;
 \path[draw] (0, 0.99) circle (0.58 );
 \draw (-3.19, 4.84) circle (0.4) (-1.45, 4.84) circle (0.4) (1.45, 4.84) circle (0.4) (3.19, 4.84) circle (0.4);
\end{tikzpicture}`,
          },
        ],
      },
      {
        name: "Nhân vật hoạt hình",
        templates: [
          {
            id: "rw-nobita",
            title: "7. Nobita",
            description: "Vẽ nhân vật Nobita.",
            code: `\\begin{tikzpicture}[scale=0.8,line width=0.3, transform shape]
% Nobita
\\definecolor{cadetblue}{rgb}{0.37, 0.62, 0.63}
\\definecolor{babyblue}{rgb}{0.54, 0.81, 0.94}
\\definecolor{bisque}{rgb}{1.0, 0.89, 0.77}
%%Doreamon
\\draw [fill=babyblue] (0.69,0.54).. controls ++(120:0.15) and ++(-
150:0.1)..(0.73,0.91).. controls ++(140:0.1) and ++(-60:0.1).. (0.47,1.16).. controls 
++(120:1.25) and ++(140:1).. (2,2.5)--(2,1)--cycle
;
\\fill[yellow!50!white] (3,1.4) rectangle ++(0.8,0.8);
%%cổ
\\fill[bisque!90!white] (2.05,1.69)--(3.18,1.95)--(3.18,1.65)--(2.4,0.85)--cycle;
\\draw[fill=white] (0.73,0.91).. controls ++(160:0.1) and ++(-70:0.12).. 
(0.48,1.18).. controls ++(105:1.1) and ++(170:0.6).. (1.92,2.15)--(2,1)--cycle
;
\\draw (0.4,1.9)--(0.76,1.8) (0.74,1.65)--(0.34,1.62) (0.78,1.47)--(0.41,1.32)
(0.78,1.06).. controls ++(170:0.45) and ++(100:0.2).. (0.82,1.35)
;
\\fill[ball color=red!40!white] (1.27,1.78) circle (0.4pt);
%%Nobita
%tay trái
\\draw[fill=bisque] 
(1.98,1.82).. controls ++(100:0.2) and ++(-60:0.1)..(1.89,2).. controls 
++(170:0.4) and ++(-90:0.1).. (1.53,1.85).. controls ++(-90:0.4) and ++(-145:0.4).. 
(1.96,1.59)--(2.1,1.7)--cycle
(1.98,1.82).. controls ++(100:0.2) and ++(90:0.1).. (1.81,1.95).. controls 
++(180:0.02) and ++(110:0.08)..(1.8,1.77).. controls ++(-30:0.06) and ++(-70:0.06).. 
(1.89,1.9)
(1.83,1.52).. controls ++(60:0.04) and ++(-60:0.04).. (1.83,1.62).. controls 
++(60:0.04) and ++(-60:0.04)..(1.83,1.75)
(1.53,1.84).. controls ++(0:0.04) and ++(160:0.06).. (1.75,1.87)
(1.6,1.72).. controls ++(-10:0.04) and ++(-160:0.06).. (1.81,1.74)
(1.63,1.59).. controls ++(-10:0.04) and ++(-160:0.04).. (1.8,1.62)
;
%Nobita
%tóc
\\fill[black!90!] (3.06,3).. controls ++(70:0.1) and ++(-180:0.04).. (3.3,3.26)--
(3.29,3.36)--(3.41,3.28).. controls ++(30:0.5) and ++(90:0.5)..(4.4,2.7)-- (4.38,2.72)--
(4.18,2.4)--(3.3,2.4)--cycle
;
\\draw[fill=white] (3.43,2.11)-- (3.58,1.87).. controls ++(60:0.03) and ++(-
20:0.03).. (3.6,2.05).. controls ++(-120:0.03) and ++(10:0.04).. (3.34,1.9).. controls 
++(100:0.04) and ++(-160:0.04)..(3.43,2.1)
;
%Mặt
\\draw[fill=bisque]
(3.26,2.78).. controls ++(80:0.1) and ++(-145:0.08).. (3.45,3.14).. controls 
++(20:0.4) and ++(120:0.4).. (4.32,2.81)--(4.15,2.41).. controls ++(10:0.1) and ++(40:0.08).. 
(4.09,2.22)
.. controls ++(-120:0.04) and ++(30:0.04).. (4,2.14)
--(4,2.14)--(3.56,2.06).. controls ++(180:0.05) and ++(-60:0.05).. (3.4,2.13)--
(3.31,2.41).. controls ++(80:0.08) and ++(-60:0.08).. (3.26,2.78)
;
\\draw (4,2.14) .. controls ++(30:0.1) and ++(-90:0.08).. (4.13,2.35);
%%miệng
\\draw[fill=pink] (3.69,2.39).. controls ++(120:0.1) and ++(20:0.06).. 
(3.4,2.57).. controls ++(-120:0.12) and ++(160:0.2).. (3.58,2.18)--cycle
;
%mắt kính
\\draw[fill=white] (3.48,2.88).. controls ++(70:0.4) and ++(70:0.35).. 
(3.91,2.78).. controls ++(-120:0.3) and ++(-100:0.35).. (3.48,2.88)
(3.93,2.77).. controls ++(55:0.35) and ++(60:0.3).. (4.22,2.58).. controls ++(-
120:0.35) and ++(-120:0.35).. (3.93,2.77)
;
\\draw[fill=black] (3.58,2.72).. controls ++(160:0.06) and ++(-180:0.06).. 
(3.6,2.85).. controls ++(-20:0.06) and ++(10:0.06).. (3.58,2.72)
(3.94,2.56).. controls ++(160:0.05) and ++(-180:0.05).. (3.98,2.69).. controls 
++(-30:0.05) and ++(10:0.05).. (3.94,2.56)
(3.41,3.28).. controls ++(90:0.04) and ++(-120:0.04).. (3.45,3.4)
;
%tròng mắt
\\fill[white] (3.58,2.74).. controls ++(160:0.02) and ++(-180:0.02).. (3.6,2.82).. 
controls ++(-20:0.02) and ++(10:0.02).. (3.58,2.74)
(3.95,2.58).. controls ++(160:0.02) and ++(-180:0.02).. (3.97,2.66).. controls 
++(-30:0.02) and ++(10:0.02).. (3.95,2.58)
;
%%tay phải
\\draw[fill=bisque]
(3.94,1.24).. controls ++(120:0.1) and ++(-30:0.1).. (3.64,1.48).. controls 
++(100:0.1) and ++(-100:0.08)..(3.7,1.85).. controls ++(120:0.06) and ++(-90:0.08).. 
(3.67,2.02).. controls ++(120:0.02) and ++(-30:0.06).. (3.59,2.06).. controls ++(100:0.04) 
and ++(-110:0.04).. (3.6,2.13)
.. controls ++(100:0.08) and ++(-110:0.1).. (3.62,2.28).. controls ++(100:0.04) 
and ++(-110:0.08).. (3.64,2.39) .. controls ++(80:0.06) and ++(140:0.05)..(3.85,2.5).. 
controls ++(-20:0.04) and ++(120:0.15).. (4.02,2.31).. controls ++(-70:0.08) and ++(60:0.1).. 
(3.92,1.9).. controls ++(-70:0.2) and ++(60:0.2).. (3.94,1.23)
;
\\draw (3.63,2.15) .. controls ++(20:0.06) and ++(-120:0.04).. (3.8,2.16) 
(3.65,2.29).. controls ++(20:0.06) and ++(-170:0.02)..(3.86,2.27) 
(3.67,2.4).. controls ++(25:0.12) and ++(-170:0.03).. (3.9,2.37)
(3.26,2.86)--(3.48,2.88) (3.53,3.08).. controls ++(50:0.2) and ++(120:0.15).. 
(3.95,3.08) (4.13,2.97).. controls ++(20:0.1) and ++(90:0.1).. (4.29,2.78)
(3.86,2.56).. controls ++(30:0.1) and ++(-30:0.1).. (3.86,2.5)
;
\\fill[fill=bisque](3.86,2.56).. controls ++(30:0.1) and ++(-30:0.1).. (3.86,2.5);
%%Ông Nobi
\\fill[white] (2.2,1.25).. controls ++(-20:0.2) and ++(-160:0.1).. (2.71,1.2)--
(2.42,0.95)--cycle;
\\draw[fill=cadetblue] (0.36,0).. controls ++(90:0.2) and ++(180:0.1).. 
(1.58,1.51).. controls ++(-60:0.1) and ++(-100:0.2).. (2.04,1.7)--(2.1,1.7).. controls ++(-
100:0.2) and ++(-120:0.1)..(2.45,1)--(2.35,0.92).. controls ++(30:0.1) and ++(-60:0.1).. 
(3.19,1.73).. controls ++(0:0.1) and ++(90:0.1).. (3.33,1.58).. controls ++(-10:0.1) and 
++(90:0.4).. (4,1).. controls ++(-45:0.2) and ++(135:0.1).. (4.44,0)--(4,0).. controls ++(90:0.2) 
and ++(30:0.1).. (2.8,0)
;
\\draw (0.9,0.49)--(1.1,0) (1.2,0).. controls ++(100:0.3) and ++(-120:0.1).. 
(1.52,1.06) (1.3,0.58).. controls ++(110:0.15) and ++(-100:0.1).. (1.31,1) (1.43,0.89)--
(1.44,1.05)
(3.54,0.88).. controls ++(90:0.1) and ++(170:0.15).. (3.88,1.3) 
(3.66,0.47).. controls ++(0:0.2) and ++(-90:0.2).. (3.96,0.89)
(3.75,0.37).. controls ++(10:0.3) and ++(100:0.1).. (4.26,0)
;
\\fill [yellow!50!white] (2.83,0.02)--(2.83,0.5)--(3.5,0.5)--(3.5,0);
\\draw[fill=white,decorate,
decoration={snake,amplitude=0.2mm,segment length=1mm}]
(2.8,0.7).. controls ++(70:0.3) and ++(120:0.3).. (3.53,0.71);
\\fill[white](2.82,0.5)--(2.82,0.7).. controls ++(10:0.3) and ++(170:0.3).. 
(3.5,0.71)--(3.5,0.5)--cycle;
\\draw (2.8,0)--(2.8,0.7).. controls ++(10:0.3) and ++(170:0.3).. (3.53,0.71)--
(3.53,0);
\\draw[fill=bisque] 
(4,0).. controls ++(90:0.06) and ++(-20:0.08).. (3.84,0.1).. controls ++(-
90:0.02) and ++(90:0.02).. (3.85,0)--cycle
(3.02,0).. controls ++(120:0.15) and ++(170:0.6).. (3.61,0.02)--(3.28,0.1).. 
controls ++(178:0.4) and ++(170:0.38).. (3.3,0.29)--(3.53,0.25).. controls ++(200:0.03) and 
++(-10:0.06).. (3.38,0.32).. controls ++(180:0.35) and ++(-160:0.1).. (3.08,0.52).. controls 
++(10:0.2) and ++(150:0.1).. (3.65,0.42).. controls ++(-60:0.2) and ++(90:0.2).. (3.85,0)--
cycle
(3.53,0.25)--(3.58,0.23)
;
\\draw[fill=white] 
(0.73,0.91).. controls ++(80:0.2) and ++(100:0.2).. (1.13,1).. controls ++(-
70:0.3) and ++(-90:0.3).. (0.73,0.91)--cycle;
\\end{tikzpicture}`,
          },
          {
            id: "rw-earth",
            title: "1. Quả địa cầu",
            description: "Mô hình quả địa cầu.",
            code: `\\begin{tikzpicture}[scale=1,transform shape]
\\definecolor{ao(english)}{rgb}{0.0, 0.5, 0.0}
\\definecolor{ceruleanblue}{rgb}{0.16, 0.32, 0.75}
\\definecolor{brown(traditional)}{rgb}{0.59, 0.29, 0.0}
\\tikzset{earth/.pic={
\\def\\D{ 
(0,0) circle(4.9cm);
}
\\fill[ball color=ceruleanblue] \\D;
\\draw\\D;
\\def\\N{ 
(-.2,4.87)
..controls +(180:1.52) and +(60:1.5) ..(-4.16,2.55) 
..controls +(-80:.5) and +(160:.5) ..(-3.7,1.75) --(-3.8,1.55) 
..controls +(-45:.5) and +(130:.5) ..(-3.45,1) 
..controls +(-20:1) and +(135:1.9) ..(-3.1,-1) 
..controls +(-100:.5) and +(85:.9) ..(-3,-2) 
..controls +(-95:.5) and +(85:.7) ..(-3.1,-3) 
..controls +(-75:.5) and +(155:.7) ..(-2.4,-4.25) --(-2.5,-3.45) 
..controls +(65:1) and +(-125:1.5) ..(-1.4,-2.1)
..controls +(15:1) and +(-140:1) ..(-.3,-.8)
..controls +(40:.4) and +(-85:.6) ..(-1.3,.3)
..controls +(95:.4) and +(-45:.6) ..(-2.6,1.2)
..controls +(145:.4) and +(-75:1.2) ..(-3.5,1.5)
..controls +(55:.4) and +(-135:.5) ..(-3.4,1.9)
..controls +(45:.2) and +(-35:.2) ..(-3.65,2.1)
..controls +(145:.6) and +(105:1) ..(-2.65,2.4)
..controls +(-75:.5) and +(-105:.6) ..(-2.45,2.9)
..controls +(45:.5) and +(-145:.6) ..(-1.5,3.3)
..controls +(35:.5) and +(-145:.6) ..(-.8,3.5)
..controls +(35:.2) and +(-100:.7) ..(-.3,3.8)
..controls +(-150:.2) and +(-130:.2) ..(-.3,4.1)
..controls +(140:.7) and +(-30:.3) ..(-1,4.15)
..controls +(-130:.7) and +(-160:.5) ..(-1.1,4.4)--(-1,4.45)--(-.9,4.4)
..controls +(30:.3) and +(140:.3) ..(-.35,4.3)--(0,4.6)--cycle
;
}
\\draw[black]\\N;
\\fill[ao(english)] \\N;
\\def\\N{ 
(2.65,4.1)
..controls +(-30:3.4) and +(32:3.3) ..(2.8,-4) 
..controls +(-148:.4) and +(-120:.3) ..(2.95,-3.1) 
..controls +(120:.4) and +(-120:.5) ..(3.3,-2) 
..controls +(120:.4) and +(-90:.6) ..(3.3,-.8) 
..controls +(100:.2) and +(20:.1) ..(3.1,-.8) 
..controls +(120:1) and +(-50:2) ..(1.5,0)
..controls +(80:1) and +(-150:.6) ..(2,1.5) 
..controls +(30:.6) and +(170:.8) ..(3.2,1.9) %(4,1.5) 
..controls +(-10:.6) and +(180:.8) ..(4.5,1.45)
..controls +(120:.6) and +(-50:.9) ..(3.9,2.1) 
..controls +(-120:.2) and +(-50:.2) ..(3.6,2.2)
..controls +(-120:.2) and +(-100:.2) ..(3.4,2.3)
..controls +(150:.4) and +(85:.4) ..(2.9,2.1)
..controls +(-160:.6) and +(-55:.6) ..(2.1,2.5)
..controls +(30:.6) and +(-140:.6) ..(2.9,2.9)
..controls +(120:.3) and +(-100:.3) ..(2.9,3.3)--(2.65,3.33)--(2.5,3.5)
..controls +(180:.3) and +(-90:.3) ..(2.2,4)--cycle
;
}
\\draw[black]\\N;
\\fill[ao(english)] \\N;
\\def\\N{ 
(0,4.9)
..controls +(0:.2) and +(165:.2) ..(1.1,4.78)--(.95,4.35) 
..controls +(-165:.7) and +(45:.6) ..(.25,3.85)
..controls +(155:.7) and +(-45:.6) ..cycle
(.7,4)
..controls +(155:.2) and +(-145:.2) ..(1,4.2)
..controls +(-45:.2) and +(90:.2) ..(1,3.9)
..controls +(155:.2) and +(-25:.2) ..cycle
(2.2,3.5)
..controls +(-30:.2) and +(125:.2) ..(2.55,3.05)
..controls +(-150:.2) and +(-80:.5) ..(2.15,3.25)--(2,3.15)--(1.9,3.25)--(2.1,3.45)
..controls +(130:.2) and +(100:.2) ..cycle
(-3,2)
..controls +(40:.2) and +(165:.8) ..(-2.2,2)
..controls +(-40:.2) and +(-165:.8) ..cycle
(-2.5,1.6)
..controls +(40:.2) and +(140:.2) ..(-2,1.7)
..controls +(-40:.2) and +(-140:.2) ..cycle
;
}
\\draw[black]\\N;
\\fill[ao(english)] \\N;
}}
\\path
(0,0)pic[scale=1]{earth};
\\end{tikzpicture}`,
          },
          {
            id: "rw-rocket",
            title: "2. Phóng tàu vũ trụ",
            description: "Mô hình phóng tàu vũ trụ.",
            code: `\\begin{tikzpicture}[scale=1,transform shape]
\\definecolor{ao(english)}{rgb}{0.0, 0.5, 0.0}
\\definecolor{ceruleanblue}{rgb}{0.16, 0.32, 0.75}
\\definecolor{brown(traditional)}{rgb}{0.59, 0.29, 0.0}
\\definecolor{bostonuniversityred}{rgb}{0.8, 0.0, 0.0}
\\definecolor{carrotorange}{rgb}{0.93, 0.57, 0.13}
\\definecolor{canaryyellow}{rgb}{1.0, 0.94, 0.0}
\\definecolor{bubbles}{rgb}{0.91, 1.0, 1.0}
\\draw (-.4,1.3)--(-2,3) node[above] {quỹ đạo}--(5.2,3);
\\draw[->] (-3,0)--(8,0) node [below]{$x$};
\\draw[->] (0,-3)--(0,7) node [left]{$y$};
\\fill (0,0)node [below left]{$O$} circle (0.4pt);
\\tikzset{earth/.pic={
\\def\\D{ 
(0,0) circle(4.9cm);
}
\\fill[ball color=ceruleanblue] \\D;
\\draw\\D;
\\draw[line width=.5mm,red,dashed] (0,0) circle(6.8cm);
\\draw[line width=.5mm,red,->] (0,-6.8)..controls +(0:10) and +(-120:20) ..(40,35) ;
\\def\\N{ 
(-.2,4.87)
..controls +(180:1.52) and +(60:1.5) ..(-4.16,2.55) 
..controls +(-80:.5) and +(160:.5) ..(-3.7,1.75) --(-3.8,1.55) 
..controls +(-45:.5) and +(130:.5) ..(-3.45,1) 
..controls +(-20:1) and +(135:1.9) ..(-3.1,-1) 
..controls +(-100:.5) and +(85:.9) ..(-3,-2) 
..controls +(-95:.5) and +(85:.7) ..(-3.1,-3) 
..controls +(-75:.5) and +(155:.7) ..(-2.4,-4.25) --(-2.5,-3.45) 
..controls +(65:1) and +(-125:1.5) ..(-1.4,-2.1)
..controls +(15:1) and +(-140:1) ..(-.3,-.8)
..controls +(40:.4) and +(-85:.6) ..(-1.3,.3)
..controls +(95:.4) and +(-45:.6) ..(-2.6,1.2)
..controls +(145:.4) and +(-75:1.2) ..(-3.5,1.5)
..controls +(55:.4) and +(-135:.5) ..(-3.4,1.9)
..controls +(45:.2) and +(-35:.2) ..(-3.65,2.1)
..controls +(145:.6) and +(105:1) ..(-2.65,2.4)
..controls +(-75:.5) and +(-105:.6) ..(-2.45,2.9)
..controls +(45:.5) and +(-145:.6) ..(-1.5,3.3)
..controls +(35:.5) and +(-145:.6) ..(-.8,3.5)
..controls +(35:.2) and +(-100:.7) ..(-.3,3.8)
..controls +(-150:.2) and +(-130:.2) ..(-.3,4.1)
..controls +(140:.7) and +(-30:.3) ..(-1,4.15)
..controls +(-130:.7) and +(-160:.5) ..(-1.1,4.4)--(-1,4.45)--(-.9,4.4)
..controls +(30:.3) and +(140:.3) ..(-.35,4.3)--(0,4.6)--cycle
;
}
\\draw[black]\\N;
\\fill[ao(english)] \\N;
\\def\\N{ 
(2.65,4.1)
..controls +(-30:3.4) and +(32:3.3) ..(2.8,-4) 
..controls +(-148:.4) and +(-120:.3) ..(2.95,-3.1) 
..controls +(120:.4) and +(-120:.5) ..(3.3,-2) 
..controls +(120:.4) and +(-90:.6) ..(3.3,-.8) 
..controls +(100:.2) and +(20:.1) ..(3.1,-.8) 
..controls +(120:1) and +(-50:2) ..(1.5,0)
..controls +(80:1) and +(-150:.6) ..(2,1.5) 
..controls +(30:.6) and +(170:.8) ..(3.2,1.9) %(4,1.5) 
..controls +(-10:.6) and +(180:.8) ..(4.5,1.45)
..controls +(120:.6) and +(-50:.9) ..(3.9,2.1) 
..controls +(-120:.2) and +(-50:.2) ..(3.6,2.2)
..controls +(-120:.2) and +(-100:.2) ..(3.4,2.3)
..controls +(150:.4) and +(85:.4) ..(2.9,2.1)
..controls +(-160:.6) and +(-55:.6) ..(2.1,2.5)
..controls +(30:.6) and +(-140:.6) ..(2.9,2.9)
..controls +(120:.3) and +(-100:.3) ..(2.9,3.3)--(2.65,3.33)--(2.5,3.5)
..controls +(180:.3) and +(-90:.3) ..(2.2,4)--cycle
;
}
\\draw[black]\\N;
\\fill[ao(english)] \\N;
\\def\\N{ 
(0,4.9)
..controls +(0:.2) and +(165:.2) ..(1.1,4.78)--(.95,4.35) 
..controls +(-165:.7) and +(45:.6) ..(.25,3.85)
..controls +(155:.7) and +(-45:.6) ..cycle
(.7,4)
..controls +(155:.2) and +(-145:.2) ..(1,4.2)
..controls +(-45:.2) and +(90:.2) ..(1,3.9)
..controls +(155:.2) and +(-25:.2) ..cycle
(2.2,3.5)
..controls +(-30:.2) and +(125:.2) ..(2.55,3.05)
..controls +(-150:.2) and +(-80:.5) ..(2.15,3.25)--(2,3.15)--(1.9,3.25)--(2.1,3.45)
..controls +(130:.2) and +(100:.2) ..cycle
(-3,2)
..controls +(40:.2) and +(165:.8) ..(-2.2,2)
..controls +(-40:.2) and +(-165:.8) ..cycle
(-2.5,1.6)
..controls +(40:.2) and +(140:.2) ..(-2,1.7)
..controls +(-40:.2) and +(-140:.2) ..cycle
;
}
\\draw[black]\\N;
\\fill[ao(english)] \\N;
}}
\\path
(0,0)pic[scale=.2]{earth};
%=====================================
\\tikzset{tau_vu_tru/.pic={
\\def\\C{ 
(-1.25,.2)
..controls +(-140:1) and +(130:.5) ..(-1.6,-2.5) --(-1.5,-2.5) --(-.85,-1.4) --cycle
;
}
\\fill[bostonuniversityred] \\C;
\\draw[red]\\C;
\\fill[xscale=-1,bostonuniversityred] \\C;
\\draw[xscale=-1,red]\\C;
\\def\\D{ 
(-.4,-1.9)
..controls +(-140:1) and +(130:.5) ..(0,-4.5) 
..controls +(50:.5) and +(-40:1) ..(.4,-1.9)--cycle
;
}
\\draw[red]\\D;
\\fill[carrotorange] \\D;
\\def\\D2{ 
(-.2,-1.9)
..controls +(-140:.7) and +(130:.2) ..(0,-3.5) 
..controls +(50:.2) and +(-40:.7) ..(.2,-1.9)--cycle
;
}
\\draw[red]\\D2;
\\fill[canaryyellow] \\D2;
\\def\\N{ 
(0,4.5)
..controls +(-150:2.5) and +(135:.8) ..(-.65,-1.8) 
..controls +(-30:.5) and +(-150:.5) ..(.65,-1.8) 
..controls +(45:.8) and +(-30:2.5) ..cycle
;
}
\\draw[black]\\N;
\\fill[bubbles] \\N;
\\def\\M{ 
(0,4.5)
..controls +(-155:.4) and +(65:.5) ..(-.95,3.4) 
..controls +(-35:.5) and +(-145:.5) ..(.95,3.4) 
..controls +(115:.5) and +(-25:.4) ..cycle
;
}
\\draw[red]\\M;
\\fill[bostonuniversityred] \\M;
\\def\\L{ 
(0,.3)
..controls +(-120:.7) and +(140:.2) ..(0,-2.4) 
..controls +(40:.2) and +(-60:.7) ..cycle
;
}
\\draw[red]\\L;
\\fill[bostonuniversityred] \\L;
\\fill (0,2) circle(7mm);
\\fill[blue] (0,2) circle(5mm);
%\\fill (0,2.3) circle(1mm);
}}
\\path
(6.7,5)pic[rotate=-33,scale=.2]{tau_vu_tru};
\\end{tikzpicture}`,
          },
          {
            id: "rw-balloon",
            title: "3. Khinh khí cầu",
            description: "Khinh khí cầu nhiều màu sắc.",
            code: `\\begin{tikzpicture}[scale=1,transform shape]
\\definecolor{byzantium}{rgb}{0.44, 0.16, 0.39}
\\definecolor{brightmaroon}{rgb}{0.76, 0.13, 0.28}
\\definecolor{atomictangerine}{rgb}{1.0, 0.6, 0.4}
\\definecolor{goldenyellow}{rgb}{1.0, 0.87, 0.0}
\\definecolor{forestgreen(web)}{rgb}{0.13, 0.55, 0.13}
\\definecolor{frenchblue}{rgb}{0.0, 0.45, 0.73}
\\definecolor{firebrick}{rgb}{0.7, 0.13, 0.13}
\\definecolor{deepcarminepink}{rgb}{0.94, 0.19, 0.22}
\\definecolor{deepcarrotorange}{rgb}{0.91, 0.41, 0.17}
\\definecolor{goldenpoppy}{rgb}{0.99, 0.76, 0.0}
\\definecolor{arsenic}{rgb}{0.23, 0.27, 0.29}
\\definecolor{antiquebrass}{rgb}{0.8, 0.58, 0.46}
\\definecolor{beaver}{rgb}{0.62, 0.51, 0.44}
\\tikzset{co_vat/.pic={
\\def\\T{ 
(-.7,-2.8)
..controls +(140:.5) and +(40:.5) ..(1,-2.7)--(.85,-2.8)
..controls +(-120:1.3) and +(-50:1.3) ..(-.45,-2.9)--cycle
;
}
\\fill[arsenic]\\T;
\\draw[black]\\T;
\\fill[atomictangerine] (-.5,-2.6)
..controls +(-30:.3) and +(-140:.3) ..(.8,-2.53)
..controls +(140:.3) and +(60:.3) ..cycle ;
\\draw[beaver] (.65,-2.5)
..controls +(-90:.2) and +(40:.2) ..(.3,-3.7)%A
(.2,-2.5)
..controls +(-90:.2) and +(40:.2) ..(.05,-3.65)%B
(-.7,-2.7)
..controls +(-70:.4) and +(120:.4) ..(-.15,-3.7)%C
;
\\draw (.3,-3.7)--(.05,-3.65)--(-.15,-3.7)--(.05,-3.75)--cycle;
%----------------------
\\draw (.3,-3.7)--(.42,-4.1);%D
\\draw (.05,-3.65)--(.07,-4);%E
\\draw (-.15,-3.7)--(-.23,-4.15);%F
\\draw[fill=antiquebrass] (.42,-4.1)--(.07,-4)--(-.23,-4.15)--(-.24,-4.65)%đáy
--(.1,-4.5)--(.45,-4.55)--cycle;
\\draw[fill=beaver] %đáy
(-.24,-4.65)--(.1,-4.5)--(.45,-4.55)--(.15,-4.7)--cycle;
\\draw (.1,-4.5)--(.07,-4);
%------------------------------------
\\def\\A{ 
(-.25,5.5)
..controls +(-172:4.7) and +(140:6) ..(-.7,-2.8)
..controls +(140:.5) and +(40:.5) ..(1,-2.7)
..controls +(45:7) and +(0:3.7) ..cycle
;
}
\\draw[black]\\A;
\\fill[byzantium] \\A;
%------------------------------------------------Red-violet <
\\def\\Rv{ 
(-.25,5.5)%đỉnh
..controls +(0:.4) and +(145:.15) ..(.7,5.3)
..controls +(170:.2) and +(0:.15) ..(.2,5.35)
..controls +(-30:.1) and +(110:.05) ..(.42,5.1)
..controls +(170:.2) and +(20:.2) ..(-.3,5.05)
--(-.32,4.7)
..controls +(170:.2) and +(20:.2) ..(-1.23,4.6)
..controls +(-110:.1) and +(80:.1) ..(-1.32,4.1)
..controls +(170:.2) and +(20:.2) ..(-2.22,3.95)
..controls +(-110:.1) and +(90:.15) ..(-2.29,3.38)
..controls +(170:.2) and +(60:.2) ..(-3.05,3.05)
..controls +(-92:.1) and +(100:.15) ..(-3.02,2.5)
..controls +(-170:.1) and +(60:.1) ..(-3.45,2.25)
..controls +(-85:.1) and +(110:.1) ..(-3.3,1.6)
..controls +(-170:.1) and +(60:.1) ..(-3.63,1.4)
..controls +(-80:.1) and +(110:.1) ..(-3.4,.75)
--(-3.52,.6)%end
..controls +(125:.15) and +(-80:.35) ..(-3.9,1.75)
--(-3.73,1.85)
..controls +(110:.15) and +(-90:.15) ..(-3.78,2.6)
..controls +(50:.1) and +(-160:.15) ..(-3.49,2.8)
..controls +(90:.2) and +(-105:.15) ..(-3.38,3.5)
..controls +(50:.1) and +(180:.05) ..(-3,3.6)
..controls +(80:.1) and +(-130:.1) ..(-2.73,4.25)
..controls +(50:.1) and +(180:.05) ..(-2.08,4.4)
..controls +(60:.2) and +(-140:.2) ..(-1.7,4.9)
..controls +(30:.1) and +(180:.1) ..(-1.1,4.95)
..controls +(60:.2) and +(-140:.2) ..(-.84,5.3)
..controls +(30:.1) and +(170:.1) ..(-.26,5.3)--cycle
}
\\draw[black!90,thin]\\Rv;
\\fill[brightmaroon] \\Rv;
%------------------------------------------------ORANGE <
\\def\\Or{ 
(-2.85,-.55)%begin orange 1
--(-2.83,-.3)
..controls +(120:.1) and +(-70:.1) ..(-3.12,.2)--(-2.85,.45)
..controls +(120:.1) and +(-70:.1) ..(-3.12,1.05)--(-2.7,1.3)
..controls +(120:.1) and +(-70:.1) ..(-2.9,1.92)--(-2.15,2.15)
..controls +(120:.1) and +(-80:.1) ..(-2.27,2.8)
..controls +(20:.15) and +(-175:.1) ..(-1.31,3)
..controls +(95:.15) and +(-92:.15) ..(-1.33,3.62)
..controls +(20:.15) and +(-175:.1) ..(-.33,3.65)--(-.32,4.2)
..controls +(20:.2) and +(170:.2) ..(.72,4.2)
..controls +(100:.1) and +(-70:.1) ..(.6,4.7)
..controls +(20:.2) and +(170:.2) ..(1.4,4.65)
..controls +(110:.1) and +(-50:.1) ..(1.19,4.95)
..controls +(20:.15) and +(160:.15) ..(1.9,4.85)
..controls +(125:.5) and +(0:.6) ..(-.25,5.5)%đỉnh
..controls +(0:.4) and +(145:.15) ..(.7,5.3)
..controls +(170:.2) and +(0:.15) ..(.2,5.35)
..controls +(-30:.1) and +(110:.05) ..(.42,5.1)
..controls +(170:.2) and +(20:.2) ..(-.3,5.05)
--(-.32,4.7)
..controls +(170:.2) and +(20:.2) ..(-1.23,4.6)
..controls +(-110:.1) and +(80:.1) ..(-1.32,4.1)
..controls +(170:.2) and +(20:.2) ..(-2.22,3.95)
..controls +(-110:.1) and +(90:.15) ..(-2.29,3.38)
..controls +(170:.2) and +(60:.2) ..(-3.05,3.05)
..controls +(-92:.1) and +(100:.15) ..(-3.02,2.5)
..controls +(-170:.1) and +(60:.1) ..(-3.45,2.25)
..controls +(-85:.1) and +(110:.1) ..(-3.3,1.6)
..controls +(-170:.1) and +(60:.1) ..(-3.63,1.4)
..controls +(-80:.1) and +(110:.1) ..(-3.4,.75)
--(-3.52,.6)%end
..controls +(-80:.1) and +(125:.35) ..cycle
}
\\draw[black!90,thin]\\Or;
\\fill[atomictangerine] \\Or;
%------------------------------------------------YELLOW <
\\def\\Ye{ 
%GY
(2.8,4.5)--(2.57,4.53)
..controls +(-50:.1) and +(120:.1) ..(2.82,4.2)
..controls +(130:.1) and +(0:.1) ..(2.27,4.35)
..controls +(-50:.1) and +(100:.1) ..(2.45,3.9)
..controls +(130:.1) and +(0:.1) ..(1.6,4.1)
..controls +(-60:.1) and +(100:.1) ..(1.7,3.53)
..controls +(130:.1) and +(0:.1) ..(.78,3.65)
..controls +(-80:.1) and +(90:.1) ..(.8,3.05)
..controls +(160:.1) and +(20:.1) ..(-.34,3.05)
--(-.32,2.45)--(-1.25,2.35)
..controls +(-80:.1) and +(100:.1) ..(-1.17,1.73)
..controls +(-150:.15) and +(0:.2) ..(-1.83,.95);
}
\\draw[black!90,thin]\\Ye;
\\fill[goldenyellow] \\Ye;
\\path (0,0) pic[scale=1]{co_vat};
\\end{tikzpicture}`,
          },
          {
            id: "convat-h23",
            title: `Con vật nghệ thuật (H23)`,
            description: `Tranh vẽ con vật (nghệ thuật)`,
            code: String.raw`\begin{tikzpicture}[
 line join=round,
 scale=1,
 transform shape,
 every node/.style={font=\normalsize}
]
 \definecolor{byzantium}{rgb}{0.44, 0.16, 0.39}
 \definecolor{brightmaroon}{rgb}{0.76, 0.13, 0.28}
 \definecolor{atomictangerine}{rgb}{1.0, 0.6, 0.4}
 \definecolor{goldenyellow}{rgb}{1.0, 0.87, 0.0}
 \definecolor{forestgreen(web)}{rgb}{0.13, 0.55, 0.13}
 \definecolor{frenchblue}{rgb}{0.0, 0.45, 0.73}
 \definecolor{firebrick}{rgb}{0.7, 0.13, 0.13}
 \definecolor{deepcarminepink}{rgb}{0.94, 0.19, 0.22}
 \definecolor{deepcarrotorange}{rgb}{0.91, 0.41, 0.17}
 \definecolor{goldenpoppy}{rgb}{0.99, 0.76, 0.0}
 \definecolor{arsenic}{rgb}{0.23, 0.27, 0.29}
 \definecolor{antiquebrass}{rgb}{0.8, 0.58, 0.46}
 \definecolor{beaver}{rgb}{0.62, 0.51, 0.44}
 \tikzset{co_vat/.pic={
 \def\T{ 
 (-.7,-2.8)
 ..controls +(140:.5) and +(40:.5) ..(1,-2.7)--(.85,-2.8)
 ..controls +(-120:1.3) and +(-50:1.3) ..(-.45,-2.9)--cycle
 }
 \fill[arsenic]\T;
 \draw[black]\T;
 \fill[atomictangerine] (-.5,-2.6)
 ..controls +(-30:.3) and +(-140:.3) ..(.8,-2.53)
 ..controls +(140:.3) and +(60:.3) ..cycle ;
 \draw[beaver] (.65,-2.5)
 ..controls +(-90:.2) and +(40:.2) ..(.3,-3.7)
 (.2,-2.5)
 ..controls +(-90:.2) and +(40:.2) ..(.05,-3.65)
 (-.7,-2.7)
 ..controls +(-70:.4) and +(120:.4) ..(-.15,-3.7)
 ;
 \draw (.3,-3.7)--(.05,-3.65)--(-.15,-3.7)--(.05,-3.75)--cycle;
 \draw (.3,-3.7)--(.42,-4.1);
 \draw (.05,-3.65)--(.07,-4);
 \draw (-.15,-3.7)--(-.23,-4.15);
 \draw[fill=antiquebrass] (.42,-4.1)--(.07,-4)--(-.23,-4.15)--(-.24,-4.65)
 --(.1,-4.5)--(.45,-4.55)--cycle;
 \draw[fill=beaver] (-.24,-4.65)--(.1,-4.5)--(.45,-4.55)--(.15,-4.7)--cycle;
 \draw (.1,-4.5)--(.07,-4);
 \def\A{ 
 (-.25,5.5)
 ..controls +(-172:4.7) and +(140:6) ..(-.7,-2.8)
 ..controls +(140:.5) and +(40:.5) ..(1,-2.7)
 ..controls +(45:7) and +(0:3.7) ..cycle
 }
 \draw[black]\A;
 \fill[byzantium] \A;
 \def\Rv{ 
 (-.25,5.5)
 ..controls +(0:.4) and +(145:.15) ..(.7,5.3)
 ..controls +(170:.2) and +(0:.15) ..(.2,5.35)
 ..controls +(-30:.1) and +(110:.05) ..(.42,5.1)
 ..controls +(170:.2) and +(20:.2) ..(-.3,5.05)
 --(-.32,4.7)
 ..controls +(170:.2) and +(20:.2) ..(-1.23,4.6)
 ..controls +(-110:.1) and +(80:.1) ..(-1.32,4.1)
 ..controls +(170:.2) and +(20:.2) ..(-2.22,3.95)
 ..controls +(-110:.1) and +(90:.15) ..(-2.29,3.38)
 ..controls +(170:.2) and +(60:.2) ..(-3.05,3.05)
 ..controls +(-92:.1) and +(100:.15) ..(-3.02,2.5)
 ..controls +(-170:.1) and +(60:.1) ..(-3.45,2.25)
 ..controls +(-85:.1) and +(110:.1) ..(-3.3,1.6)
 ..controls +(-170:.1) and +(60:.1) ..(-3.63,1.4)
 ..controls +(-80:.1) and +(110:.1) ..(-3.4,.75)
 --(-3.52,.6)
 ..controls +(125:.15) and +(-80:.35) ..(-3.9,1.75)
 --(-3.73,1.85)
 ..controls +(110:.15) and +(-90:.15) ..(-3.78,2.6)
 ..controls +(50:.1) and +(-160:.15) ..(-3.49,2.8)
 ..controls +(90:.2) and +(-105:.15) ..(-3.38,3.5)
 ..controls +(50:.1) and +(180:.05) ..(-3,3.6)
 ..controls +(80:.1) and +(-130:.1) ..(-2.73,4.25)
 ..controls +(50:.1) and +(180:.05) ..(-2.08,4.4)
 ..controls +(60:.2) and +(-140:.2) ..(-1.7,4.9)
 ..controls +(30:.1) and +(180:.1) ..(-1.1,4.95)
 ..controls +(60:.2) and +(-140:.2) ..(-.84,5.3)
 ..controls +(30:.1) and +(170:.1) ..(-.26,5.3)--cycle
 }
 \draw[black!90,thin]\Rv;
 \fill[brightmaroon] \Rv;
 \def\Or{ 
 (-2.85,-.55)
 --(-2.83,-.3)
 ..controls +(120:.1) and +(-70:.1) ..(-3.12,.2)--(-2.85,.45)
 ..controls +(120:.1) and +(-70:.1) ..(-3.12,1.05)--(-2.7,1.3)
 ..controls +(120:.1) and +(-70:.1) ..(-2.9,1.92)--(-2.15,2.15)
 ..controls +(120:.1) and +(-80:.1) ..(-2.27,2.8)
 ..controls +(20:.15) and +(-175:.1) ..(-1.31,3)
 ..controls +(95:.15) and +(-92:.15) ..(-1.33,3.62)
 ..controls +(20:.15) and +(-175:.1) ..(-.33,3.65)--(-.32,4.2)
 ..controls +(20:.2) and +(170:.2) ..(.72,4.2)
 ..controls +(100:.1) and +(-70:.1) ..(.6,4.7)
 ..controls +(20:.2) and +(170:.2) ..(1.4,4.65)
 ..controls +(110:.1) and +(-50:.1) ..(1.19,4.95)
 ..controls +(20:.15) and +(160:.15) ..(1.9,4.85)
 ..controls +(125:.5) and +(0:.6) ..(-.25,5.5)
 ..controls +(0:.4) and +(145:.15) ..(.7,5.3)
 ..controls +(170:.2) and +(0:.15) ..(.2,5.35)
 ..controls +(-30:.1) and +(110:.05) ..(.42,5.1)
 ..controls +(170:.2) and +(20:.2) ..(-.3,5.05)
 --(-.32,4.7)
 ..controls +(170:.2) and +(20:.2) ..(-1.23,4.6)
 ..controls +(-110:.1) and +(80:.1) ..(-1.32,4.1)
 ..controls +(170:.2) and +(20:.2) ..(-2.22,3.95)
 ..controls +(-110:.1) and +(90:.15) ..(-2.29,3.38)
 ..controls +(170:.2) and +(60:.2) ..(-3.05,3.05)
 ..controls +(-92:.1) and +(100:.15) ..(-3.02,2.5)
 ..controls +(-170:.1) and +(60:.1) ..(-3.45,2.25)
 ..controls +(-85:.1) and +(110:.1) ..(-3.3,1.6)
 ..controls +(-170:.1) and +(60:.1) ..(-3.63,1.4)
 ..controls +(-80:.1) and +(110:.1) ..(-3.4,.75)
 --(-3.52,.6)
 ..controls +(-80:.1) and +(125:.35) ..cycle
 }
 \draw[black!90,thin]\Or;
 \fill[atomictangerine] \Or;
 \def\Ye{ 
 (2.8,4.5)--(2.57,4.53)
 ..controls +(-50:.1) and +(120:.1) ..(2.82,4.2)
 ..controls +(130:.1) and +(0:.1) ..(2.27,4.35)
 ..controls +(-50:.1) and +(100:.1) ..(2.45,3.9)
 ..controls +(130:.1) and +(0:.1) ..(1.6,4.1)
 ..controls +(-60:.1) and +(100:.1) ..(1.7,3.53)
 ..controls +(130:.1) and +(0:.1) ..(.78,3.65)
 ..controls +(-80:.1) and +(90:.1) ..(.8,3.05)
 ..controls +(160:.1) and +(20:.1) ..(-.34,3.05)
 --(-.32,2.45)--(-1.25,2.35)
 ..controls +(-80:.1) and +(100:.1) ..(-1.17,1.73)
 ..controls +(-150:.15) and +(0:.2) ..(-1.83,.95);
 }
 \draw[black!90,thin]\Ye;
 \fill[goldenyellow] \Ye;
 }}
 \path (0,0) pic[scale=1]{co_vat};
\end{tikzpicture}`,
          },
        ],
      },
    ],
  },
];
