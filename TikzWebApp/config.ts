import type { Category } from './types';

// Danh sách các email được phép truy cập Thư viện của người tạo app
export const ALLOWED_EMAILS: string[] = [
  'totoancvabd@gmail.com', // Email của người tạo
  // Thêm các email khác vào đây, ví dụ: 'hocsinh1@gmail.com'
];

// Dữ liệu Hướng dẫn sử dụng mặc định
export const DEFAULT_GUIDE_DATA = {
  videoLink: '',
  fileLink: ''
};

// Dữ liệu Thư viện của người tạo app (được hardcode để chia sẻ cho những người có email hợp lệ)
// Người tạo app có thể copy dữ liệu từ localStorage ('TIKZ_USER_LIBRARY') và dán vào đây để chia sẻ.
export const CREATOR_LIBRARY_DATA: Category = {
  id: 'shared-library',
  name: 'Thư viện chung',
  subCategories: [
    {
      name: 'Styles phổ biến',
      templates: [
        {
          id: 'style-arrow',
          title: 'Mũi tên chuẩn',
          description: 'Style mũi tên myarrow',
          code: `myarrow/.style={-stealth, thick, blue}`
        },
        {
          id: 'style-node',
          title: 'Node chuẩn',
          description: 'Style node mynode',
          code: `mynode/.style={circle, draw, fill=white}`
        }
      ]
    },
    {
      name: 'Bảng biến thiên (tkz-tab)',
      templates: [
        {
          id: 'tkz-tab-1',
          title: 'Bảng biến thiên cơ bản',
          description: 'Bảng biến thiên cơ bản với tkz-tab',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.3, espcl=2, deltacl=0.4]
{$x$/0.7, $h(x)'$/0.7, $h(x)$/1.7}
{$0$, $3$, $6$, $8$}
\\tkzTabLine
{, +, 0, -, 0, +,}
\\tkzTabVar
{-/$0$, +/$405$, -/$324$, +/$480$}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-2',
          title: 'Xét dấu nhiều biểu thức',
          description: 'Bảng xét dấu nhiều biểu thức',
          code: `\\begin{tikzpicture}
\\tkzTabInit[lgt=1.7, espcl=2, deltacl=0]
{$x$/0.7, $(x-2)^2$/0.7, $x+3$/0.7,$\\dfrac{(x-2)^2}{x+3}$/1}
{,$-3$, $2$,}
\\tkzTabLine{, +, 0, +, 0, +,}
\\tkzTabLine{, -, 0, +, 0, +,}
\\tkzTabLine{, -, d, +,0, +,}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-3',
          title: 'Bảng biến thiên có vô cực',
          description: 'Bảng biến thiên có vô cực',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1, espcl=1.5, deltacl=.5]
{$x$/0.7, $y'$/0.7, $y$/1.6}
{$-\\infty$, $-1$, $0$, $1$, $+\\infty$}
\\tkzTabLine
{, -, 0, +, 0, -, 0, +, }
\\tkzTabVar
{+/$+\\infty$, -/$-1$, +/$0$, -/$-1$, +/$+\\infty$}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-4',
          title: 'Bảng biến thiên có gián đoạn',
          description: 'Bảng biến thiên có điểm gián đoạn (d)',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.3, espcl=2.7, deltacl=0.5]
{$x$/0.7, $C(x)'$/0.7, $C(x)$/2}
{$0$, $80$, $120$}
\\tkzTabLine
{ d, -, 0, +, }
\\tkzTabVar
{D+/$+\\infty$, -/$400$, +/$\\dfrac{1300}{3}$}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-5',
          title: 'Bảng biến thiên tùy biến (path/node)',
          description: 'Bảng biến thiên dùng path và node để vẽ mũi tên tùy biến',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,espcl=3]
{$ x $/0.75, $ f'(x) $/2.3}
{$ -\\infty $, $ -3 $, $ -1 $, $ +\\infty $}
\\path([yshift=6pt]N12) node[circle] (A1) {$ -\\infty $}
([yshift=-9pt]N21) node[circle] (A2) {$ -1 $}
([yshift=25pt]N32) node[circle,inner sep=0pt] (A3) {$ -\\frac{61}{3} $}
([yshift=-9pt]N41) node[circle] (A4) {$ +\\infty $};
\\foreach \\i/\\j in {1/2,2/3,3/4}
\\draw[-Stealth] (A\\i)--(A\\j); % Mũi tên stealth
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-6',
          title: 'Bảng biến thiên bỏ đoạn',
          description: 'Bảng biến thiên có vùng bỏ đi (h)',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,,lgt=1.5,espcl=2.5,deltacl=0.5]
{$x$/0.7, $f(x)$/0.7, $f'(x)$/2}
{$-\\infty$, $-1$, $1$, $2$, }
\\tkzTabLine{,-,0,h,d,+,d,h,}
\\tkzTabVar{+/$+\\infty$ ,-H/, D-/$-\\infty$ , +H/$+4$ , }
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-7',
          title: 'Bài toán tổng quát',
          description: 'Bảng biến thiên tổng quát với pattern',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.5, espcl=3, deltacl=0.5]
{$x$/0.7, $f(x)'$/0.7, $f(x)$/4}
{$-\\infty$, $x_1$, $x_2$,$x_3$,$x_4$,$x_5$, $+\\infty$}
\\tkzTabLine
{,+, 0, -, d , +,0,-,0, , ,+,}
\\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] 
([xshift=0pt,yshift=0pt]N51) rectangle ([xshift=0pt,yshift=0pt]N63) ;
\\path
([xshift=0pt,yshift=10pt]N13) node[inner sep=3pt] (A1) {$-\\infty$}
([xshift=0pt,yshift=-25pt]N22) node[circle,inner sep=1pt] (A2) {$f(x_1)$}
([xshift=0pt,yshift=-60pt]N32) node[circle,inner sep=1pt] (A3) {$f(x_2)$}
([xshift=0pt,yshift=-10pt]N42) node[circle,inner sep=1pt] (A4) {$f(x_3)$}
([xshift=0pt,yshift=10pt]N53) 
node[fill=white, text centered, minimum width=0.5cm, minimum 
height=0.3cm] (A5) {$f(x_4)$}
([xshift=15pt,yshift=10pt]N63) node (A6) {$f(x_5)$}
([xshift=0pt,yshift=-10pt]N72) node[circle,inner sep=1pt] (A7) {$+\\infty$};
\\draw [double] (N61)--(N62)--(N63);
\\foreach \\i/\\j in {1/2,3/4,4/5,6/7}
\\draw[-Stealth] (A\\i)--(A\\j); 
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-8',
          title: 'Bảng biến thiên hàm căn bậc hai',
          description: 'Bảng biến thiên hàm căn bậc hai',
          code: `\\begin{tikzpicture}[font=\\large, declare function={f(\\x)=\\x-sqrt(8-\\x^2);}]
\\tkzTabInit[nocadre=false, lgt=1.0, espcl=3, deltacl=0.6]
{\\large $x$/1.0, \\large $y'$/0.7, \\large $y$/2.5}
{\\large $-2\\sqrt{2}$, \\large $-2$, \\large $2\\sqrt{2}$}
\\large{\\tkzTabLine{, -, 0, +, }}

\\draw[double distance=1pt, double=white] (N11) -- (N12);
\\draw[double distance=1pt, double=white] (N31) -- (N32);

\\path
([yshift=-25pt]N12) node (A1) {\\large $-2\\sqrt{2}$}
([yshift=8pt]N23) node (A2) {\\large $-4$}
([yshift=-8pt]N32) node (A3) {\\large $2\\sqrt{2}$};

\\foreach \\i/\\j in {1/2, 2/3} {
    \\draw[-Stealth] (A\\i) -- (A\\j);
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-9',
          title: 'Bảng biến thiên giá trị tùy ý 1',
          description: 'Bảng biến thiên với các giá trị tùy ý, có nhãn min/max',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.5, espcl=3, deltacl=0.5]
{$x$/0.7, $h(x)'$/0.7, $h(x)$/3.2}
{$0$, $3$, $6$, $8$}
\\tkzTabLine
{ ,+, 0, -, 0, +}
\\path([yshift=18pt]N13) node[circle,inner sep=1pt] (A1) {$0$}
([yshift=-18pt]N22) node[circle,inner sep=1pt] (A2) {$405$}
([yshift=38pt]N33) node[circle,inner sep=1pt] (A3) {$ 324$}
([yshift=-9pt]N42) node[draw=red] (A4) {$480$};
\\foreach \\i/\\j in {1/2,2/3,3/4}
\\draw[-Stealth] (A\\i)--(A\\j); 
\\foreach \\i/\\label in {1/min, 2/CĐ, 3/CT, 4/max} {
\\node[below=-1pt of A\\i] {\\label};
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-10',
          title: 'Bảng biến thiên giá trị tùy ý 2 (có màu)',
          description: 'Bảng biến thiên với các giá trị tùy ý, có màu sắc',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.5, espcl=3, deltacl=0.5]
{$x$/0.7, $h(x)'$/0.7, $h(x)$/3.2}
{$0$, $3$, $6$, $8$}
\\tkzTabLine
{ ,+, 0, -, 0, +}
\\path
([yshift=18pt]N13) node[circle,inner sep=0.5pt] (A1) {$0$}
([yshift=-20pt]N22) node[draw=blue,circle,inner sep=1pt] (A2) {$405$}
([yshift=-50pt]N32) node[circle,inner sep=0.5pt] (A3) {$ 324$}
([yshift=-10pt]N42) node[draw=red,inner sep=3pt] (A4) {$480$};
\\foreach \\i/\\j in {1/2,2/3,3/4}
\\draw[-Stealth] (A\\i)--(A\\j); 
\\foreach \\i/\\label in {1/min, 2/CĐ, 3/CT, 4/max} {
\\node[below=-1pt of A\\i] {\\label};
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-11',
          title: 'Bảng biến thiên giá trị tùy ý 3 (có màu, box)',
          description: 'Bảng biến thiên với các giá trị tùy ý, có màu sắc và box',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.5, espcl=3, deltacl=0.5]
{$x$/0.7, $h(x)'$/0.7, $h(x)$/3.5}
{$0$, $3$, $6$, $8$}
\\tkzTabLine
{ ,+, 0, -, 0, +}
\\path
([yshift=20pt,xshift=0pt]N13) node[draw=red,inner sep=4pt] (A1) {$0$}
([yshift=70pt,xshift=0pt]N23) node[draw=blue,circle,inner sep=1pt] (A2) {$405$}
([yshift=45pt,xshift=0pt]N33) node[draw=teal,circle,inner sep=1pt] (A3) {$324$}
([yshift=90pt,xshift=0pt]N43) node[draw=red,inner sep=3pt] (A4) {$480$};
\\draw (-0,1) rectangle (3,3);
\\foreach \\i/\\j in {1/2,2/3,3/4}
\\draw[-Stealth] (A\\i)--(A\\j); 
\\foreach \\i/\\label in {1/min, 2/CĐ, 3/CT, 4/max} {
\\node[below=-1pt of A\\i] {\\label};
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-12',
          title: 'Bảng biến thiên giá trị tùy ý 4 (có gạch sọc)',
          description: 'Bảng biến thiên với các giá trị tùy ý, có vùng gạch sọc',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.5, espcl=3, deltacl=0.5]
{$x$/0.7, $h(x)'$/0.7, $h(x)$/3.5}
{$0$, $3$, $6$, $8$}
\\tkzTabLine
{ ,+, , -, 0, +}
\\path
([xshift=0pt,yshift=20pt]N13) node[draw=red,inner sep=4pt] (A1) {$0$}
([xshift=-11pt,yshift=88pt]N23) node[draw=blue,circle,inner sep=1pt] (A2) {$405$}
([xshift=0pt,yshift=11pt]N33) node[draw=teal,fill=white ,inner sep=1pt] (A3) {$324$}
([xshift=0pt,yshift=90pt]N43) node[draw=red,inner sep=3pt] (A4) {$480$};
\\draw [double] (N21)--(N23);
\\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] 
([xshift=0pt,yshift=0pt]N21) rectangle ([xshift=0pt,yshift=0pt]N33) ;
\\foreach \\i/\\j in {1/2,3/4}
\\draw[-Stealth] (A\\i)--(A\\j); 
\\node[draw, fill=white, text centered, minimum width=0.5cm, minimum height=0.3cm] at ([xshift=0pt,yshift=8pt]N33) {$324$};
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-13',
          title: 'Bảng biến thiên tổng quát 2',
          description: 'Bảng biến thiên tổng quát với nhiều vùng gạch sọc',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.5, espcl=3, deltacl=0.5]
{$x$/0.7, $f(x)'$/0.7, $f(x)$/4.2}
{$-\\infty$, $x_1$, $x_2$,$x_3$,$x_4$,$x_5$, $+\\infty$}
\\tkzTabLine
{,+, d, , 0 , +,0,-,0, , ,+,}
\\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] 
([xshift=0pt,yshift=0pt]N51) rectangle ([xshift=0pt,yshift=0pt]N63) ;
\\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] 
([xshift=0pt,yshift=0pt]N21) rectangle ([xshift=0pt,yshift=0pt]N33) ;
\\path
([xshift=0pt,yshift=10pt]N13) node[inner sep=3pt] (A1) {$-\\infty$}
([xshift=-13pt,yshift=-25pt]N22) node[inner sep=1pt] (A2) {$f(x_1)$}
([xshift=0pt,yshift=-60pt]N32) node[fill=white] (A3) {$f(x_2)$}
([xshift=0pt,yshift=-10pt]N42) node[circle,inner sep=1pt] (A4) {$f(x_3)$}
([xshift=0pt,yshift=10pt]N53) 
node[fill=white] (A5) {$f(x_4)$}
([xshift=15pt,yshift=10pt]N63) node (A6) {$f(x_5)$}
([xshift=0pt,yshift=-10pt]N72) node[circle,inner sep=1pt] (A7) {$+\\infty$};
\\draw [double] 
(N61)--(N62)--(N63) (N21)--(N22)--(N23) ;
\\foreach \\i/\\j in {1/2,3/4,4/5,6/7}
\\draw[-Stealth] (A\\i)--(A\\j); 
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-14',
          title: 'Bảng biến thiên tổng quát tùy biến',
          description: 'Bảng biến thiên tổng quát với nhiều tùy biến phức tạp',
          code: `\\begin{tikzpicture}
\\tkzTabInit[nocadre=false,lgt=1.6, espcl=3, deltacl=0.5]
{$x$/0.8, $f'(x)$/0.8, $f(x)$/4.5}
{$-\\infty$, $x_1$, $x_2$,$x_3$,$x_4$,$x_5$, $+\\infty$}
\\tkzTabLine
{,+, d, , +, ,-, , , ,+,}
\\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] 
([xshift=0cm,yshift=0cm]N21) rectangle ([xshift=0cm,yshift=0cm]N33) ;
\\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] 
([xshift=0cm,yshift=0cm]N51) rectangle ([xshift=0cm,yshift=0cm]N63) ;
\\path
([xshift=0cm,yshift=-0.4cm]N31) node[fill=white] (A8) {$0$}
([xshift=0cm,yshift=-0.4cm]N51) node[fill=white] (A9) {$0$}
([xshift=0cm,yshift=-0.4cm]N41) node[fill=white] (A10) {$0$}
([xshift=0cm,yshift=0.3cm]N13) node[inner sep=0.1cm] (A1) {$-\\infty$}
([xshift=-0.5cm,yshift=-1.5cm]N22) node[inner sep=0.03cm] (A2) {$f(x_1)$}
([xshift=0cm,yshift=-3cm]N32) node[fill=white] (A3) {$f(x_2)$}
([xshift=0cm,yshift=-0.3cm]N42) node[circle,inner sep=0.03cm] (A4) {$f(x_3)$}
([xshift=0cm,yshift=0.3cm]N53) 
node[fill=white] (A5) {$f(x_4)$}
([xshift=0.5cm,yshift=0.3cm]N63) node (A6) {$f(x_5)$}
([xshift=0cm,yshift=-0.3cm]N72) node[circle,inner sep=0.03cm] (A7) {$+\\infty$};
\\draw [double] 
(N61)--(N62)--(N63) (N21)--(N22)--(N23) ;
\\foreach \\i/\\j in {1/2,3/4,4/5,6/7}
\\draw[-Stealth] (A\\i)--(A\\j); 
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-15',
          title: 'Bảng biến thiên hàm căn bậc 2 (lấy khoảng ngoài)',
          description: 'Bảng biến thiên hàm căn bậc 2 với pattern gạch chéo',
          code: `\\begin{tikzpicture}[font=\\large, declare function={f(\\x)=sqrt(\\x^2-4*\\x+3);}]
\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.5]
{\\large $x$/0.7, \\large $y'$/0.7, \\large $y$/2.}
{\\large $-\\infty$, \\large $1$, \\large $3$, \\large $+\\infty$}
\\large{\\tkzTabLine{, -, , , , +, }}
\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] (N21) rectangle (N33);
\\draw[double distance=1pt, double=white] (N21) -- (N22);
\\draw[double distance=1pt, double=white] (N31) -- (N32);
\\path
([yshift=-7pt]N12) node (A1) {\\large $+\\infty$}
([yshift=7pt]N23) node[fill=white, inner sep=2pt] (A2) {\\large $0$}
([yshift=7pt]N33) node[fill=white, inner sep=2pt] (A3) {\\large $0$}
([yshift=-7pt]N42) node (A4) {\\large $+\\infty$};
\\foreach \\i/\\j in {1/2, 3/4} {
 \\draw[-Stealth] (A\\i) -- (A\\j);
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-16',
          title: 'Bảng biến thiên hàm căn bậc 2 (bỏ giữa chuẩn)',
          description: 'Bảng biến thiên hàm căn bậc 2 với pattern gạch chéo và che cạnh dưới',
          code: `\\begin{tikzpicture}[font=\\large, declare function={f(\\x)=sqrt(\\x^2-4*\\x+3);}]
\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.5]
{\\large $x$/0.7, \\large $y'$/0.7, \\large $y$/2.}
{\\large $-\\infty$, \\large $1$, \\large $3$, \\large $+\\infty$}
\\large{\\tkzTabLine{, -, , , , +, }}
\\draw[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] (N21) rectangle (N33);
% Vẽ đường trắng để che cạnh dưới của pattern
\\draw[white, line width=1pt] (N23) -- (N33);
\\draw[white, line width=1pt] (N22) -- (N23);
\\draw[white, line width=1pt] (N32) -- (N33);
\\draw[double distance=1pt, double=white] (N21) -- (N22);
\\draw[double distance=1pt, double=white] (N31) -- (N32);
\\path
([yshift=-7pt]N12) node (A1) {\\large $+\\infty$}
([yshift=7pt]N23) node[fill=white, inner sep=2pt] (A2) {\\large $0$}
([yshift=7pt]N33) node[fill=white, inner sep=2pt] (A3) {\\large $0$}
([yshift=-7pt]N42) node (A4) {\\large $+\\infty$};
\\foreach \\i/\\j in {1/2, 3/4} {
 \\draw[-Stealth] (A\\i) -- (A\\j);
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-17',
          title: 'Bảng biến thiên hàm tùy ý (trên khoảng)',
          description: 'Bảng biến thiên hàm số trên một khoảng với đường tiệm cận đứng',
          code: `\\begin{tikzpicture}[font=\\large, declare function={f(\\x)=16000/\\x+2.5*\\x;}]
\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.3]
{\\large $x$/0.7, \\large $y'$/0.7, \\large $y$/2.}
{\\large $0$, \\large $80$, \\large $120$}
\\large{\\tkzTabLine{d, -, 0, +, }}

\\draw[double distance=1pt, double=white] (N11) -- (N13);

\\path
([xshift= 14pt, yshift=-7pt]N12) node (A1) {\\large $+\\infty$}
([yshift=7pt]N23) node (A2) {\\large $400$}
([yshift=35pt]N33) node (A3) {\\large $\\dfrac{1300}{3}$};

\\foreach \\i/\\j in {1/2, 2/3} {
    \\draw[-Stealth] (A\\i) -- (A\\j);
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-18',
          title: 'Bảng biến thiên hàm B1/B2',
          description: 'Bảng biến thiên hàm số bậc 1 trên bậc 2 với hai đường tiệm cận đứng',
          code: `\\begin{tikzpicture}[font=\\large, declare function={f(\\x)=(2*\\x-3)/(5*\\x^2-15*\\x+10);}]
\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.5]
{\\large $x$/0.7, \\large $y'$/0.7, \\large $y$/2.}
{\\large $-\\infty$, \\large $1$, \\large $2$, \\large $+\\infty$}
\\large{\\tkzTabLine{, -, d, -, d, -, }}

\\draw[double distance=1pt, double=white] (N21) -- (N23);
\\draw[double distance=1pt, double=white] (N31) -- (N33);

\\path
([yshift=-7pt]N12) node (A1) {\\large $0$}
([xshift=-14pt, yshift=7pt]N23) node (A2) {\\large $-\\infty$}
([xshift=12pt, yshift=-7pt]N22) node (A3) {\\large $+\\infty$}
([xshift=-14pt, yshift=7pt]N33) node (A4) {\\large $-\\infty$}
([xshift=12pt, yshift=-7pt]N32) node (A5) {\\large $+\\infty$}
([yshift=7pt]N43) node (A6) {\\large $0$};

\\foreach \\i/\\j in {1/2, 3/4, 5/6} {
    \\draw[-Stealth] (A\\i) -- (A\\j);
}
\\end{tikzpicture}`
        },
        {
          id: 'tkz-tab-19',
          title: 'Bảng biến thiên hàm B2/B2',
          description: 'Bảng biến thiên hàm số bậc 2 trên bậc 2',
          code: `\\begin{tikzpicture}[font=\\large, declare function={f(\\x)=(16*(\\x)^2-8*\\x)/(16*(\\x)^2+1);}]
\\tkzTabInit[nocadre=false, lgt=1., espcl=3., deltacl=0.6]
{\\large $x$/1.2, \\large $y'$/0.7, \\large $y$/3.}
{\\large $-\\infty$, \\large $\\dfrac{-1-\\sqrt{5}}{8}$, \\large $\\dfrac{-1+\\sqrt{5}}{8}$, \\large $+\\infty$}
\\large{\\tkzTabLine{, +, 0, -, 0, +, }}

\\path
([yshift=-40pt]N12) node (A1) {\\large $1$}
([yshift=-17pt]N22) node (A2) {\\large $\\dfrac{1+\\sqrt{5}}{2}$}
([yshift=17pt]N33) node (A3) {\\large $\\dfrac{1-\\sqrt{5}}{2}$}
([yshift=-40pt]N42) node (A4) {\\large $1$};

\\foreach \\i/\\j in {1/2, 2/3, 3/4} {
    \\draw[-Stealth] (A\\i) -- (A\\j);
}
\\end{tikzpicture}`
        }
      ]
    }
  ]
};
