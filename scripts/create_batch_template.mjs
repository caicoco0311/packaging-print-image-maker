#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const output = process.argv[2];
const previewPath = process.argv[3];
if (!output) throw new Error("Usage: create_batch_template.mjs <output.xlsx> [preview.png]");

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Batch Input");
sheet.showGridLines = false;
const headers = ["task_id", "user_input", "enabled", "material", "palette", "finish", "notes", "output_name"];
const rows = [
  ["WINE-001", "红酒 + Label", true, "", "", "", "", "wine-label"],
  ["PEPTIDE-001", "肽 + Label", true, "cotton paper", "warm ivory, burgundy", "gold foil", "", "peptide-label"],
  ["COFFEE-001", "咖啡 + Box", false, "", "", "", "Example disabled row", "coffee-box"],
];
sheet.getRange("A1:H4").values = [headers, ...rows];
sheet.getRange("A1:H1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
};
sheet.getRange("A2:H4").format = { verticalAlignment: "top", wrapText: false };
sheet.getRange("A1:H4").format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
sheet.getRange("A:A").format.columnWidth = 18;
sheet.getRange("B:B").format.columnWidth = 30;
sheet.getRange("C:C").format.columnWidth = 12;
sheet.getRange("D:G").format.columnWidth = 24;
sheet.getRange("H:H").format.columnWidth = 20;
sheet.getRange("C2:C200").dataValidation = { rule: { type: "list", values: ["TRUE", "FALSE"] } };
sheet.freezePanes.freezeRows(1);
sheet.tables.add("A1:H4", true, "BatchInputTable");

await fs.mkdir(path.dirname(path.resolve(output)), { recursive: true });
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(output);
if (previewPath) {
  const preview = await workbook.render({ sheetName: "Batch Input", autoCrop: "all", scale: 1.5, format: "png" });
  await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
}
console.log(path.resolve(output));
