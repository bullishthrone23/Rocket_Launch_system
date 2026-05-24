Rocket Launch Simulation System
	A powerful and lightweight 2D orbital mechanics simulator. This project allows you to model multi-stage rocket flights, calculate trajectory dynamics including 	atmospheric drag, and visualize mission outcomes with high precision.

Overview:
	The Rocket Launch Simulation System is a two-part software suite designed to simulate rocket flight dynamics. The core engine, written in C, performs complex physical 	calculations—such as gravity, multi-stage thrust, fuel consumption, and aerodynamic drag—while the Python integration automatically visualizes the mission trajectory in 	real-time.

Key Features:

	Multi-Stage Engine: Define multiple rocket stages with specific dry mass, fuel capacity, thrust, and burn-time parameters.

	Atmospheric Drag Model: Implements an exponential atmospheric density model to simulate aerodynamic resistance (drag) based on altitude and velocity.

	GNC (Guidance, Navigation, and Control) Sequencer: A deterministic Finite State Machine (FSM) that automatically handles launch, coasting, and orbital insertion phases.

	Physics-Based Engine: Uses a 2-body gravitational model and variable mass differential equations to simulate realistic flight paths.

	Intelligent Visualization: Automatic generation of 2D mission plots using Matplotlib.

	Data Logging: All telemetry (time, altitude, velocity, fuel levels) is logged to a CSV file for post-flight analysis.

Technical Stack:

	Core Simulator: C (C99 standard)

	Visualization: Python 3 (Pandas, Matplotlib, NumPy)

	Inter-process communication: Automated system calls

Prerequisites

	Python 3.x installed on your system.

	Required Python libraries:
		pip install pandas matplotlib numpy

License
	This project is open-source and available for educational use. Feel free to fork, modify, and improve the simulation logic!