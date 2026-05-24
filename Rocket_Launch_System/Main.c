#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <windows.h>
#include <shellapi.h>

typedef struct {
    double dry_mass, fuel_mass, thrust, burn_time, mass_flow_rate, target_pitch, change_rate;
} Stage;

static void strip_filename(char *path) {
    char *sep = strrchr(path, '\\');
    if (sep) *sep = '\0';
}

int main() {
    double R = 6371000.0, mu = 3.986004418e14, PI = 3.141592653589793;
    // drag coefficient, reference area, scale height, sea level density
    double drag_coeff = 0.5, ref_area = 10.75, scale_height = 8500.0, rho0 = 1.225;
    
    char exe_path[4096], exe_dir[4096], csv_path[4096], traj_script[4096];
    GetModuleFileNameA(NULL, exe_path, MAX_PATH);
    strcpy(exe_dir, exe_path);
    strip_filename(exe_dir); 

    
    strcpy(csv_path, exe_dir);
    strcat(csv_path, "\\\\simulation_results.csv");

    
    char parent_dir[4096];
    strcpy(parent_dir, exe_dir);
    
    strip_filename(parent_dir);
    
    strcpy(traj_script, parent_dir);
    strcat(traj_script, "\\\\Trajectory_Graph.py");

    int num;
    printf("Enter the number of rocket stages: ");
    scanf("%d", &num);
    Stage *s = (Stage*)malloc(num * sizeof(Stage));
    for(int i=0; i<num; i++) {
        printf("\n--- STAGE %d ---\n", i+1);
        printf("Enter dry mass (kg): "); scanf("%lf", &s[i].dry_mass);
        printf("Enter fuel mass (kg): "); scanf("%lf", &s[i].fuel_mass);
        printf("Enter thrust (N): "); scanf("%lf", &s[i].thrust);
        printf("Enter burn time (s): "); scanf("%lf", &s[i].burn_time);
        printf("Enter the TARGET PITCH (deg): "); scanf("%lf", &s[i].target_pitch);
        printf("Enter the PITCH CHANGE RATE (deg/s): "); scanf("%lf", &s[i].change_rate);
        s[i].mass_flow_rate = s[i].fuel_mass / s[i].burn_time;
    }

    int mission;
    printf("\nChoose mission: 1 = Orbit, 2 = Escape: ");
    scanf("%d", &mission);
    double sim_time;
    printf("Enter the simulation time (s): ");
    scanf("%lf", &sim_time);

    double x = 0, y = R, vx = 0, vy = 0, pitch = 90, time = 0, dt = 0.1;
    int stage = 0, phase = 0;
    double ign_time = 0;

    FILE *f = fopen(csv_path, "w");
    // create (if needed) a reports folder inside exe_dir and put TXT reports there
    char reports_dir[4096];
    strcpy(reports_dir, exe_dir);
    strcat(reports_dir, "\\\\reports");
    CreateDirectoryA(reports_dir, NULL);

    char txt_path[4096];
    strcpy(txt_path, reports_dir);
    strcat(txt_path, "\\\\simulation_results.txt");
    FILE *ft = fopen(txt_path, "w");

    // Write a more descriptive, tabular CSV header with units (velocity in km/h)
    fprintf(f, "Time_s,Pos_X_m,Pos_Y_m,Altitude_m,Velocity_kmh,Acceleration_m_s2,Fuel_kg,Phase\n");

    // Write a pretty TXT header (fixed-width columns)
    if (ft) {
        fprintf(ft, "%-10s %-12s %-12s %-12s %-14s %-18s %-10s %-6s\n",
            "Time(s)", "Pos_X(m)", "Pos_Y(m)", "Alt(m)", "Vel(km/h)", "Accel(m/s^2)", "Fuel(kg)", "Phase");
        fprintf(ft, "%-10s %-12s %-12s %-12s %-14s %-18s %-10s %-6s\n",
            "----------", "------------", "------------", "------------", "--------------", "------------------", "----------", "------");
    }

    double prev_speed_m_s = 0.0;

    while(time < sim_time) {
        double r = sqrt(x*x + y*y);
        double alt = r - R;
        double vel = sqrt(vx*vx + vy*vy);
        
        // Phase transitions
        if (mission == 1) {
            if (phase == 0 && stage == 1 && (time - ign_time) > 30.0) phase = 1;
            if (phase == 1 && (x*vx + y*vy)/r <= 0.0) phase = 2;
            if (phase == 2 && vel >= sqrt(mu/r) * 0.995) phase = 3;
        } else {
            if (phase == 0 && stage == 1 && (time - ign_time) > 30.0) phase = 1;
            if (phase == 1 && vel >= sqrt(2.0*mu/r) * 0.995) phase = 2;
        }

        // Drag calculation
        double rho = (alt < 100000.0) ? rho0 * exp(-alt / scale_height) : 0.0;
        double drag = 0.5 * rho * vel * vel * drag_coeff * ref_area;
        double dx = (vel > 0) ? (drag * (vx / vel)) : 0;
        double dy = (vel > 0) ? (drag * (vy / vel)) : 0;

        // thrust and fuel consumption
        double thrust = 0;
        if ((phase == 0 || phase == 2) && s[stage].fuel_mass > 0) {
            thrust = s[stage].thrust;
            s[stage].fuel_mass -= s[stage].mass_flow_rate * dt;
        } else if (phase == 0 && stage == 0 && s[0].fuel_mass <= 0) {
            stage = 1; ign_time = time;
        }

        // Pitch
        if (mission == 1 && phase == 2) pitch = 0;
        else if (pitch > s[stage].target_pitch) pitch -= s[stage].change_rate * dt;
        
        double angle = atan2(y, x) - (90 - pitch) * PI / 180.0;
        double mass = s[stage].dry_mass + s[stage].fuel_mass;
        
        // drag calculation is already vectorized, so we can directly use dx and dy in the equations of motion
        vx += ((thrust * cos(angle) - dx) / mass - (mu/pow(r,3))*x) * dt;
        vy += ((thrust * sin(angle) - dy) / mass - (mu/pow(r,3))*y) * dt;
        x += vx * dt; y += vy * dt;

        // compute altitude, speed (both m/s and km/h), acceleration for tabular output
        double altitude = alt; // meters above sea level
        double speed_m_s = vel; // m/s
        double speed_kmh = speed_m_s * 3.6; // km/h
        double acceleration = (time > 0.0) ? (speed_m_s - prev_speed_m_s) / dt : 0.0;
        prev_speed_m_s = speed_m_s;

        // Write CSV (velocity in km/h)
        fprintf(f, "%.3f,%.3f,%.3f,%.3f,%.3f,%.6f,%.3f,%d\n", time, x, y, altitude, speed_kmh, acceleration, s[stage].fuel_mass, phase);

        // Write aligned TXT row if file opened
        if (ft) {
            fprintf(ft, "%-10.3f %-12.3f %-12.3f %-12.3f %-14.3f %-18.6f %-10.3f %-6d\n",
                time, x, y, altitude, speed_kmh, acceleration, s[stage].fuel_mass, phase);
        }
        time += dt;
        if (alt < 0 && time > 10) break;
    }
    fclose(f);
    if (ft) fclose(ft);

    // Ensure reports dir exists and move any txt report there
    CreateDirectoryA(reports_dir, NULL);
    char possible_src[4096];
    strcpy(possible_src, exe_dir);
    strcat(possible_src, "\\\\simulation_results.txt");
    char dest_path[4096];
    strcpy(dest_path, reports_dir);
    strcat(dest_path, "\\\\simulation_results.txt");
    // Move if exists (ignore failure)
    MoveFileA(possible_src, dest_path);
    
    // Ensure an images folder exists inside the exe directory (usually output/images)
    char images_dir[4096];
    strcpy(images_dir, exe_dir);
    strcat(images_dir, "\\\\images");
    // CreateDirectoryA returns nonzero on success; ignore errors (folder may already exist)
    CreateDirectoryA(images_dir, NULL);

    // Try launching the Python scripts using ShellExecute for better reliability
    char params[12288];
    // pass: <script> <csv_path> <images_dir>
    sprintf(params, "\"%s\" \"%s\" \"%s\"", traj_script, csv_path, images_dir);
    HINSTANCE res = ShellExecuteA(NULL, "open", "py", params, NULL, SW_SHOWNORMAL);
    if ((intptr_t)res <= 32) {
        // fallback to "python" if the "py" launcher is not available
        ShellExecuteA(NULL, "open", "python", params, NULL, SW_SHOWNORMAL);
    }

    // Also launch the Grafic_Result.py script to generate saved graphs
    char grafic_script[4096];
    strcpy(grafic_script, parent_dir);
    strcat(grafic_script, "\\\\Grafic_Result.py");

    char params2[12288];
    sprintf(params2, "\"%s\" \"%s\" \"%s\"", grafic_script, csv_path, images_dir);
    HINSTANCE res2 = ShellExecuteA(NULL, "open", "py", params2, NULL, SW_SHOWNORMAL);
    if ((intptr_t)res2 <= 32) {
        ShellExecuteA(NULL, "open", "python", params2, NULL, SW_SHOWNORMAL);
    }
    
    free(s);
    return 0;
}