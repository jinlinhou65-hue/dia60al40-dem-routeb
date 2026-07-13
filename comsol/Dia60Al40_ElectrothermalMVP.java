import com.comsol.model.Model;
import com.comsol.model.util.ModelUtil;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public class Dia60Al40_ElectrothermalMVP {
    private Model model;
    private double widthUm;
    private double heightUm;
    private double meshHmaxUm = 8.0;
    private double meshHminUm = 1.0;
    private double appliedVoltageV = 0.1;
    private String interpolationPath;
    private String outputDir;

    public static void main(String[] args) throws Exception {
        if (args.length != 2 && args.length != 4 && args.length != 5) {
            throw new IllegalArgumentException(
                "usage: <property-grid.csv> <output-directory> "
                + "[mesh-hmax-um mesh-hmin-um [applied-voltage-v]]"
            );
        }
        Dia60Al40_ElectrothermalMVP app = new Dia60Al40_ElectrothermalMVP();
        app.outputDir = args[1];
        if (args.length == 4) {
            app.meshHmaxUm = Double.parseDouble(args[2]);
            app.meshHminUm = Double.parseDouble(args[3]);
        }
        if (args.length == 5) {
            app.meshHmaxUm = Double.parseDouble(args[2]);
            app.meshHminUm = Double.parseDouble(args[3]);
            app.appliedVoltageV = Double.parseDouble(args[4]);
        }
        if (app.meshHmaxUm <= 0.0 || app.meshHminUm <= 0.0 || app.meshHminUm > app.meshHmaxUm) {
            throw new IllegalArgumentException("mesh sizes must satisfy 0 < hmin <= hmax");
        }
        if (!Double.isFinite(app.appliedVoltageV) || app.appliedVoltageV <= 0.0) {
            throw new IllegalArgumentException("applied voltage must be finite and positive");
        }
        app.readGrid(args[0]);
        app.buildAndSolve();
    }

    private static void log(String message) {
        System.err.println(message);
    }

    private void readGrid(String path) throws Exception {
        log("[INPUT] " + path);
        BufferedReader reader = new BufferedReader(new FileReader(path));
        String header = reader.readLine();
        if (header == null) {
            reader.close();
            throw new IllegalArgumentException("property grid is empty");
        }
        String[] names = header.split(",");
        Map<String, Integer> columns = new HashMap<String, Integer>();
        for (int index = 0; index < names.length; index++) {
            columns.put(names[index].trim(), index);
        }
        String line;
        int rowCount = 0;
        widthUm = 0.0;
        heightUm = 0.0;
        while ((line = reader.readLine()) != null) {
            if (line.trim().isEmpty()) {
                continue;
            }
            String[] values = line.split(",");
            double x = Double.parseDouble(values[columns.get("x_um")]);
            double y = Double.parseDouble(values[columns.get("y_um")]);
            double sigma = Double.parseDouble(values[columns.get("sigma_s_m")]);
            double thermal = Double.parseDouble(values[columns.get("k_w_mk")]);
            if (sigma <= 0.0 || thermal <= 0.0) {
                reader.close();
                throw new IllegalArgumentException("conductivity values must be positive");
            }
            rowCount++;
            widthUm = Math.max(widthUm, x);
            heightUm = Math.max(heightUm, y);
        }
        reader.close();
        if (rowCount == 0 || widthUm <= 0.0 || heightUm <= 0.0) {
            throw new IllegalArgumentException("property grid dimensions are invalid");
        }
        File gridFile = new File(path);
        interpolationPath = new File(gridFile.getParentFile(), "stage5_comsol_interpolation.txt").getAbsolutePath();
        if (!new File(interpolationPath).isFile()) {
            throw new IllegalArgumentException("missing COMSOL interpolation file " + interpolationPath);
        }
        log(String.format(Locale.US, "[GRID] rows=%d width_um=%.6f height_um=%.6f", rowCount, widthUm, heightUm));
    }

    private void buildAndSolve() throws Exception {
        File directory = new File(outputDir);
        if (!directory.isDirectory() && !directory.mkdirs()) {
            throw new IllegalArgumentException("cannot create output directory " + outputDir);
        }
        model = ModelUtil.create("Dia60Al40ElectrothermalMVP");
        model.modelPath(outputDir);
        defineParameters();
        defineInterpolationFunctions();
        defineGeometryAndSelections();
        defineMaterial();
        definePhysics();
        defineMeshAndStudy();
        log("[SOLVE] start");
        model.study("std1").run();
        log("[SOLVE] OK");
        exportResults();
        model.save(new File(directory, "Dia60Al40_ElectrothermalMVP.mph").getAbsolutePath());
        log("[SAVE] OK");
    }

    private void defineParameters() {
        model.param().set("W", widthUm + "[um]");
        model.param().set("H", heightUm + "[um]");
        model.param().set("Vapp", appliedVoltageV + "[V]");
        model.param().set("Tamb", "293.15[K]");
        model.param().set("rho_eff", "2700[kg/m^3]");
        model.param().set("Cp_eff", "900[J/(kg*K)]");
    }

    private void defineInterpolationFunctions() {
        model.func().create("props", "Interpolation");
        model.func("props").set("source", "file");
        model.func("props").set("filename", interpolationPath);
        model.func("props").set("struct", "spreadsheet");
        model.func("props").set("nargs", 2);
        model.func("props").set("funcs", new String[][] {{"sigma_map", "1"}, {"k_map", "2"}});
        model.func("props").set("interp", "linear");
        model.func("props").set("extrap", "const");
        model.func("props").set("argunit", new String[] {"um", "um"});
        model.func("props").set("fununit", new String[] {"S/m", "W/(m*K)"});
        model.func("props").importData();
    }

    private void defineGeometryAndSelections() {
        model.component().create("comp1", true);
        model.component("comp1").geom().create("geom1", 2);
        model.component("comp1").geom("geom1").lengthUnit("um");
        model.component("comp1").geom("geom1").create("r1", "Rectangle");
        model.component("comp1").geom("geom1").feature("r1").set("size", new String[] {"W", "H"});
        model.component("comp1").geom("geom1").run();
        createBoundaryBox("sel_bottom", -0.1, widthUm + 0.1, -0.1, 0.1);
        createBoundaryBox("sel_top", -0.1, widthUm + 0.1, heightUm - 0.1, heightUm + 0.1);
        model.component("comp1").selection().create("sel_electrodes", "Union");
        model.component("comp1").selection("sel_electrodes").set("entitydim", 1);
        model.component("comp1").selection("sel_electrodes").set("input", new String[] {"sel_bottom", "sel_top"});
    }

    private void createBoundaryBox(String tag, double xmin, double xmax, double ymin, double ymax) {
        model.component("comp1").selection().create(tag, "Box");
        model.component("comp1").selection(tag).set("entitydim", 1);
        model.component("comp1").selection(tag).set("xmin", xmin + "[um]");
        model.component("comp1").selection(tag).set("xmax", xmax + "[um]");
        model.component("comp1").selection(tag).set("ymin", ymin + "[um]");
        model.component("comp1").selection(tag).set("ymax", ymax + "[um]");
        model.component("comp1").selection(tag).set("condition", "inside");
    }

    private void defineMaterial() {
        model.component("comp1").material().create("mat1", "Common");
        model.component("comp1").material("mat1").propertyGroup("def").set("electricconductivity", "sigma_map(x,y)");
        model.component("comp1").material("mat1").propertyGroup("def").set("thermalconductivity", "k_map(x,y)");
        model.component("comp1").material("mat1").propertyGroup("def").set("density", "rho_eff");
        model.component("comp1").material("mat1").propertyGroup("def").set("heatcapacity", "Cp_eff");
    }

    private void definePhysics() {
        model.component("comp1").physics().create("ec", "ConductiveMedia", "geom1");
        model.component("comp1").physics("ec").create("pot1", "ElectricPotential", 1);
        model.component("comp1").physics("ec").feature("pot1").selection().named("sel_top");
        model.component("comp1").physics("ec").feature("pot1").set("V0", "Vapp");
        model.component("comp1").physics("ec").create("gnd1", "Ground", 1);
        model.component("comp1").physics("ec").feature("gnd1").selection().named("sel_bottom");

        model.component("comp1").physics().create("ht", "HeatTransfer", "geom1");
        model.component("comp1").physics("ht").create("temp1", "TemperatureBoundary", 1);
        model.component("comp1").physics("ht").feature("temp1").selection().named("sel_electrodes");
        model.component("comp1").physics("ht").feature("temp1").set("T0", "Tamb");
        model.component("comp1").multiphysics().create("emh1", "ElectromagneticHeatSource");
        model.component("comp1").multiphysics("emh1").selection().all();
    }

    private void defineMeshAndStudy() {
        model.component("comp1").mesh().create("mesh1");
        model.component("comp1").mesh("mesh1").create("ftri1", "FreeTri");
        model.component("comp1").mesh("mesh1").feature("size").set("hmax", meshHmaxUm + "[um]");
        model.component("comp1").mesh("mesh1").feature("size").set("hmin", meshHminUm + "[um]");
        model.component("comp1").mesh("mesh1").run();
        model.study().create("std1");
        model.study("std1").create("stat", "Stationary");
    }

    private void exportResults() throws Exception {
        File directory = new File(outputDir);
        model.result().create("pgV", "PlotGroup2D");
        model.result("pgV").create("surf1", "Surface");
        model.result("pgV").feature("surf1").set("expr", "V");
        model.result().create("pgT", "PlotGroup2D");
        model.result("pgT").create("surf1", "Surface");
        model.result("pgT").feature("surf1").set("expr", "T");
        model.result().create("pgQ", "PlotGroup2D");
        model.result("pgQ").create("surf1", "Surface");
        model.result("pgQ").feature("surf1").set("expr", "ec.Qh");

        exportImage("imgV", "pgV", new File(directory, "comsol_potential.png").getAbsolutePath());
        exportImage("imgT", "pgT", new File(directory, "comsol_temperature.png").getAbsolutePath());
        exportImage("imgQ", "pgQ", new File(directory, "comsol_joule_heat.png").getAbsolutePath());

        model.result().export().create("data1", "Data");
        model.result().export("data1").set("expr", new String[] {"V", "T", "ec.normJ", "ec.Qh", "sigma_map(x,y)", "k_map(x,y)"});
        model.result().export("data1").set("filename", new File(directory, "comsol_fields.csv").getAbsolutePath());
        model.result().export("data1").run();

        model.result().numerical().create("maxT", "MaxSurface");
        model.result().numerical("maxT").set("expr", "T");
        model.result().numerical("maxT").selection().all();
        double maxTemperature = model.result().numerical("maxT").getReal()[0][0];
        model.result().numerical().create("intQ", "IntSurface");
        model.result().numerical("intQ").set("expr", "ec.Qh");
        model.result().numerical("intQ").selection().all();
        double integratedJoule = model.result().numerical("intQ").getReal()[0][0];
        double inferredTopCurrent = integratedJoule / appliedVoltageV;
        FileWriter writer = new FileWriter(new File(directory, "comsol_summary.json"));
        writer.write(String.format(Locale.US,
            "{\n  \"solver\": \"COMSOL 6.4\",\n  \"model\": \"homogenized_contact_network_electrothermal_mvp\",\n  \"mesh_hmax_um\": %.12g,\n  \"mesh_hmin_um\": %.12g,\n  \"applied_voltage_v\": %.12g,\n  \"ambient_temperature_k\": 293.15,\n  \"max_temperature_k\": %.12g,\n  \"integrated_joule_2d_w_per_m_depth\": %.12g,\n  \"top_current_a_per_m_depth\": %.12g,\n  \"current_inference\": \"integrated_joule_divided_by_applied_voltage\",\n  \"solve_status\": \"success\"\n}\n",
            meshHmaxUm, meshHminUm, appliedVoltageV, maxTemperature, integratedJoule,
            inferredTopCurrent));
        writer.close();
        log(String.format(Locale.US,
            "[RESULT] Vapp_V=%.9g maxT_K=%.9g intQ_W_per_m=%.9g current_A_per_m=%.9g",
            appliedVoltageV, maxTemperature, integratedJoule, inferredTopCurrent));
    }

    private void exportImage(String tag, String plotGroup, String filename) {
        model.result().export().create(tag, "Image2D");
        model.result().export(tag).set("plotgroup", plotGroup);
        model.result().export(tag).set("pngfilename", filename);
        model.result().export(tag).set("width", 1000);
        model.result().export(tag).set("height", 650);
        model.result().export(tag).run();
    }
}
