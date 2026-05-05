\documentclass[11pt,a4paper]{article}

% --- Packages ---
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{enumitem}
\usepackage{titlesec}

% --- Colors ---
\definecolor{linkblue}{HTML}{1F6FEB}
\definecolor{codebg}{HTML}{F4F4F4}
\definecolor{codetext}{HTML}{1F2937}

\hypersetup{
    colorlinks=true,
    linkcolor=linkblue,
    urlcolor=linkblue,
    citecolor=linkblue
}

% --- Code listing style ---
\lstset{
    basicstyle=\ttfamily\small\color{codetext},
    backgroundcolor=\color{codebg},
    frame=single,
    framerule=0pt,
    breaklines=true,
    columns=fullflexible,
    xleftmargin=8pt,
    xrightmargin=8pt,
    aboveskip=8pt,
    belowskip=8pt
}

% --- Title formatting ---
\titleformat{\section}{\Large\bfseries}{}{0pt}{}
\titleformat{\subsection}{\large\bfseries}{}{0pt}{}
\setlength{\parskip}{6pt}
\setlength{\parindent}{0pt}

% --- Document ---
\title{\textbf{SCADA Control Center}}
\author{Sara Ewaida \\ \small Computer Engineering, Birzeit University}
\date{}

\begin{document}
\maketitle

A live web-based \textbf{Supervisory Control and Data Acquisition (SCADA)} dashboard built in Python. It simulates a small industrial process, polls five sensors on a one-second scan cycle, stores every reading in a time-series historian, and visualises the live state of the plant in a browser-based HMI.

This project demonstrates the core building blocks of a real SCADA system on a small scale: the \textbf{field layer} (sensors), the \textbf{historian} (data persistence), and the \textbf{HMI} (operator interface), all communicating through a clean, decoupled architecture.

\section*{Dashboard Preview}

\begin{center}
\includegraphics[width=\linewidth]{screenshots/dashboard_overview.png}
\end{center}

\section*{Features}

\begin{itemize}[leftmargin=*]
    \item \textbf{Live process monitoring} --- current values for every tag, refreshed every second.
    \item \textbf{Industrial alarm system} --- each tag is classified as \texttt{NORMAL}, \texttt{WARNING}, or \texttt{CRITICAL} based on configurable hi/lo limits, with colour-coded indicators on the dashboard.
    \item \textbf{Active alarms panel} --- only deviating tags are shown, the way real SCADA systems summarise plant health.
    \item \textbf{Time-series trends} --- the last two minutes of data plotted for every tag, with reference lines for warning and critical limits.
    \item \textbf{Historian database} --- every reading is logged to a SQLite database (\texttt{historian.db}) so historical data persists across restarts.
    \item \textbf{Realistic sensor simulation} --- each tag uses a mean-reverting random walk plus occasional process upset events, so values move the way real instruments do.
    \item \textbf{Dark industrial HMI theme} --- visual style modelled on real SCADA control room interfaces.
\end{itemize}

\section*{Architecture}

\begin{lstlisting}
   +----------------------+       +----------------------+
   |   Sensor Simulator   |  -->  |  Background Poller   |
   |   (5 process tags)   |       |       (1 Hz)         |
   +----------------------+       +----------+-----------+
                                             |
                                             v
                                  +----------------------+
                                  |   Historian (SQLite) |
                                  +----------+-----------+
                                             |
                                             v
                                  +----------------------+
                                  |    Dash + Plotly     |
                                  |   (HMI / Browser)    |
                                  +----------------------+
\end{lstlisting}

The poller runs in a background thread and writes to the historian on every scan cycle. The Dash app runs independently and reads from the historian when it refreshes the UI. This separation mirrors how real SCADA systems decouple acquisition from presentation.

\section*{Process Variables (Tags)}

\begin{center}
\begin{tabular}{@{}llcccc@{}}
\toprule
\textbf{Tag} & \textbf{Description} & \textbf{Unit} & \textbf{Setpoint} & \textbf{Warning Range} & \textbf{Critical Range} \\
\midrule
TT-101 & Reactor Temperature & C     & 75   & 65 -- 85       & 60 -- 90       \\
PT-201 & Pump Pressure       & bar   & 5.0  & 4.0 -- 6.0     & 3.0 -- 7.0     \\
FT-301 & Flow Rate           & L/min & 100  & 90 -- 110      & 80 -- 120      \\
LT-401 & Tank Level          & \%    & 60   & 30 -- 85       & 15 -- 95       \\
ST-501 & Motor Speed         & RPM   & 1500 & 1300 -- 1700   & 1100 -- 1900   \\
\bottomrule
\end{tabular}
\end{center}

The tag naming follows ISA-style conventions (\texttt{TT} = Temperature Transmitter, \texttt{PT} = Pressure Transmitter, \texttt{FT} = Flow Transmitter, \texttt{LT} = Level Transmitter, \texttt{ST} = Speed Transmitter).

\section*{Tech Stack}

\begin{itemize}[leftmargin=*]
    \item \textbf{Python 3} --- application language
    \item \textbf{Dash} --- web framework for the HMI
    \item \textbf{Plotly} --- interactive trend charts
    \item \textbf{SQLite} --- embedded historian database
    \item \textbf{threading} --- background scan cycle
\end{itemize}

\section*{How to Run}

\subsection*{Prerequisites}

\begin{itemize}[leftmargin=*]
    \item Python 3.9 or newer
    \item \texttt{pip} package manager
\end{itemize}

\subsection*{Setup}

\begin{lstlisting}
git clone https://github.com/SaraEwaida/scada-dashboard.git
cd scada-dashboard
pip install -r requirements.txt
\end{lstlisting}

\subsection*{Run}

\begin{lstlisting}
python app.py
\end{lstlisting}

Open a browser and navigate to:

\begin{lstlisting}
http://127.0.0.1:8050
\end{lstlisting}

The dashboard will appear with live data updating every second. To stop the application, press \texttt{Ctrl + C} in the terminal.

\section*{Project Structure}

\begin{lstlisting}
scada-dashboard/
+-- app.py                 # Dash application and HMI layout
+-- sensor_simulator.py    # Process variable simulator with realistic noise
+-- database.py            # SQLite historian (init, log, query)
+-- requirements.txt       # Python dependencies
+-- historian.db           # Generated at runtime - holds logged readings
+-- screenshots/           # Dashboard screenshots
+-- README.md
\end{lstlisting}

\section*{Possible Extensions}

The current project is a foundation that can grow toward a more complete SCADA system:

\begin{itemize}[leftmargin=*]
    \item \textbf{Modbus TCP ingestion} --- replace the simulator with real Modbus polling using \texttt{pymodbus}, so the dashboard can monitor real PLCs or industrial devices.
    \item \textbf{Operator setpoint controls} --- add UI controls so operators can change setpoints from the dashboard.
    \item \textbf{Alarm acknowledgment and event log} --- track when alarms occurred, who acknowledged them, and when they cleared.
    \item \textbf{User authentication and roles} --- separate operator and engineer privilege levels.
    \item \textbf{Trend export} --- let operators export historical data as CSV for reporting.
\end{itemize}

\section*{Author}

\textbf{Sara Ewaida} --- Computer Engineering, Birzeit University \\
GitHub: \href{https://github.com/SaraEwaida}{@SaraEwaida}

\end{document}
