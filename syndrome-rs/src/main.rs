//! Syndrome CLI
//!
//! Command-line interface for the Syndrome framework.

use syndrome::prelude::*;
use std::env;

fn print_header() {
    println!("╔═══════════════════════════════════════════════════════════════╗");
    println!("║                    SYNDROME FRAMEWORK                         ║");
    println!("║  Categorical Resolution of Disease Trajectories through       ║");
    println!("║  Partition Geometry and Oscillator Coherence                  ║");
    println!("╚═══════════════════════════════════════════════════════════════╝");
    println!();
}

fn demo_partition() {
    println!("═══ Partition Coordinate System ═══\n");

    // Demonstrate capacity formula
    println!("Capacity C(n) = 2n² for depths 1-5:");
    for n in 1..=5 {
        let cap = partition_capacity(n);
        println!("  C({}) = {}", n, cap);
    }
    println!();

    // Demonstrate state enumeration
    println!("States at n=2:");
    let states = enumerate_partition_states(2);
    for (i, state) in states.iter().enumerate() {
        println!("  [{}] n={}, ℓ={}, m={}, s={:+.1}",
            i, state.n(), state.ell(), state.m(),
            if state.chirality() == Chirality::Plus { 0.5 } else { -0.5 });
    }
    println!();

    // Demonstrate address encoding
    println!("Ternary address encoding:");
    let test_values = [0.1, 0.5, 0.718, 0.9];
    for &val in &test_values {
        let address = value_to_address(val, 5, 0.0, 1.0).unwrap();
        let recovered = address_to_value(&address, 0.0, 1.0).unwrap();
        println!("  {:.3} → {:?} → {:.5} (error: {:.2e})",
            val, address, recovered, (val - recovered).abs());
    }
    println!();
}

fn demo_coherence() {
    println!("═══ Universal Coherence Equation ═══\n");

    println!("η = (Π_obs - Π_deg) / (Π_opt - Π_deg)\n");

    // Example coherence calculations
    let examples = [
        (0.8, 1.0, 0.0, "Healthy cell"),
        (0.5, 1.0, 0.0, "Moderate dysfunction"),
        (0.2, 1.0, 0.0, "Severe dysfunction"),
        (0.9, 1.0, 0.2, "With elevated baseline"),
    ];

    for (pi_obs, pi_opt, pi_deg, label) in examples {
        let eta = coherence_index(pi_obs, pi_opt, pi_deg);
        println!("  {}: η = {:.3}", label, eta);
    }
    println!();

    // Oscillator classes
    println!("Eight Oscillator Classes:");
    let classes = [
        (OscillatorClass::Protein, "Protein (P)", "Misfolding diseases"),
        (OscillatorClass::Enzyme, "Enzyme (E)", "Metabolic diseases"),
        (OscillatorClass::Channel, "Channel (C)", "Channelopathies"),
        (OscillatorClass::Membrane, "Membrane (M)", "Excitability disorders"),
        (OscillatorClass::Atp, "ATP (A)", "Mitochondrial diseases"),
        (OscillatorClass::Genetic, "Genetic (G)", "Expression disorders"),
        (OscillatorClass::Calcium, "Calcium (Ca)", "Signaling disorders"),
        (OscillatorClass::Circadian, "Circadian (R)", "Rhythm disorders"),
    ];

    for (_, name, disease_type) in classes {
        println!("  {} → {}", name, disease_type);
    }
    println!();
}

fn demo_disease_vector() {
    println!("═══ Disease Vector Analysis ═══\n");

    // Create example disease profiles
    let alzheimers = DiseaseVector::new(
        0.85, // Protein (high - misfolding)
        0.25, // Enzyme
        0.15, // Channel
        0.30, // Membrane
        0.55, // ATP (elevated - mitochondrial involvement)
        0.20, // Genetic
        0.45, // Calcium (elevated - Ca dysregulation)
        0.15, // Circadian
    ).unwrap();

    let diabetes = DiseaseVector::new(
        0.20, // Protein
        0.80, // Enzyme (high - metabolic)
        0.15, // Channel
        0.25, // Membrane
        0.45, // ATP
        0.30, // Genetic
        0.35, // Calcium
        0.20, // Circadian
    ).unwrap();

    println!("Alzheimer's Disease Profile:");
    print_disease_profile(&alzheimers);

    println!("Type 2 Diabetes Profile:");
    print_disease_profile(&diabetes);

    // Compute signature distance
    let dist = disease_signature_distance(&alzheimers, &diabetes);
    println!("Disease signature distance: {:.4}\n", dist);
}

fn print_disease_profile(d: &DiseaseVector) {
    let arr = d.to_array();
    let labels = ["P", "E", "C", "M", "A", "G", "Ca", "R"];

    print!("  [");
    for (i, &val) in arr.iter().enumerate() {
        if i > 0 { print!(", "); }
        print!("{}:{:.2}", labels[i], val);
    }
    println!("]");

    let (code, name, _) = d.classification();
    println!("  Dominant class: {} ({})", code, name);
    println!("  Severity: {:.3}\n", d.severity(None));
}

fn demo_trajectory() {
    println!("═══ Trajectory Computation (COMPLETE Algorithm) ═══\n");

    // Create S-entropy waypoints
    let start = SEntropyPoint::new(0.1, 0.1, 0.1).unwrap();
    let end = SEntropyPoint::new(0.8, 0.7, 0.9).unwrap();

    println!("Trajectory from ({:.1}, {:.1}, {:.1}) to ({:.1}, {:.1}, {:.1})",
        start.s_k, start.s_t, start.s_e,
        end.s_k, end.s_t, end.s_e);
    println!();

    // Run COMPLETE algorithm
    let constraints = vec![
        Constraint::tissue(),
        Constraint::custom("precision", 0.01),
    ];

    match complete_trajectory(start, end, constraints, 20) {
        Ok(traj) => {
            println!("COMPLETE algorithm results:");
            println!("  Max depth achieved: {}", traj.max_depth);
            println!("  Precision: {:.2e}", traj.precision());
            println!("  Trajectory length: {:.4}", traj.length);
            println!("  Complete: {}", traj.complete);

            println!("\n  Constraint satisfaction:");
            for c in &traj.constraints {
                println!("    {} (depth ≥ {}): {}",
                    c.id, c.min_depth,
                    if c.satisfied { "✓" } else { "✗" });
            }

            // Sample trajectory
            println!("\n  Trajectory samples:");
            let samples = traj.sample(5);
            for (i, s) in samples.iter().enumerate() {
                println!("    t={:.2}: ({:.3}, {:.3}, {:.3})",
                    i as f64 / 4.0, s.s_k, s.s_t, s.s_e);
            }
        }
        Err(e) => {
            println!("  Error: {}", e);
        }
    }
    println!();
}

fn demo_therapeutic() {
    println!("═══ Therapeutic Efficacy ═══\n");

    // Example treatment scenarios
    let scenarios = [
        (0.3, 0.7, 0.95, "Highly effective treatment"),
        (0.3, 0.5, 0.95, "Moderately effective treatment"),
        (0.3, 0.35, 0.95, "Minimally effective treatment"),
        (0.3, 0.25, 0.95, "Harmful treatment (worsens coherence)"),
    ];

    println!("Treatment efficacy E = (η_treated - η_untreated) / (η_healthy - η_untreated)\n");

    for (eta_untreated, eta_treated, eta_healthy, label) in scenarios {
        let efficacy = therapeutic_efficacy(eta_treated, eta_untreated, eta_healthy);
        let bar_len = ((efficacy.abs() * 20.0) as usize).min(20);
        let bar = if efficacy >= 0.0 {
            format!("[{}{}]", "█".repeat(bar_len), " ".repeat(20 - bar_len))
        } else {
            format!("[{}{}]", " ".repeat(20 - bar_len), "░".repeat(bar_len))
        };
        println!("  {}: E = {:+.2} {}", label, efficacy, bar);
    }
    println!();

    // Predicted coherence
    println!("Predicted coherence after treatment:");
    println!("  η_pred = η + E·α·(1-η)  where α is treatment strength\n");

    let eta_baseline = 0.4;
    let efficacy = 0.7;
    for alpha in [0.25, 0.5, 0.75, 1.0] {
        let eta_pred = predicted_coherence_after_treatment(eta_baseline, efficacy, alpha);
        println!("  α = {:.2}: η = {:.2} → η_pred = {:.3}", alpha, eta_baseline, eta_pred);
    }
    println!();
}

fn print_help() {
    println!("Usage: syndrome-cli [COMMAND]\n");
    println!("Commands:");
    println!("  demo        Run full demonstration");
    println!("  partition   Demonstrate partition coordinates");
    println!("  coherence   Demonstrate coherence computation");
    println!("  disease     Demonstrate disease vectors");
    println!("  trajectory  Demonstrate trajectory computation");
    println!("  therapeutic Demonstrate therapeutic efficacy");
    println!("  help        Show this help message");
    println!();
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(|s| s.as_str()).unwrap_or("demo");

    match command {
        "demo" | "all" => {
            print_header();
            demo_partition();
            demo_coherence();
            demo_disease_vector();
            demo_trajectory();
            demo_therapeutic();
            println!("═══════════════════════════════════════════════════════════════");
            println!("  Framework demonstration complete.");
            println!("═══════════════════════════════════════════════════════════════");
        }
        "partition" => {
            print_header();
            demo_partition();
        }
        "coherence" => {
            print_header();
            demo_coherence();
        }
        "disease" => {
            print_header();
            demo_disease_vector();
        }
        "trajectory" => {
            print_header();
            demo_trajectory();
        }
        "therapeutic" => {
            print_header();
            demo_therapeutic();
        }
        "help" | "--help" | "-h" => {
            print_header();
            print_help();
        }
        _ => {
            eprintln!("Unknown command: {}", command);
            print_help();
            std::process::exit(1);
        }
    }
}
