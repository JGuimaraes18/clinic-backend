import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Sun, Moon, Laptop, Palette, Layout, Type, Save } from "lucide-react";
import { toast } from "sonner";

const COLORS = [
  { name: "Sálvia", hex: "#6B9E7F" },
  { name: "Azul Real", hex: "#0651ED" },
  { name: "Índigo", hex: "#6366F1" },
  { name: "Violeta", hex: "#8B5CF6" },
  { name: "Esmeralda", hex: "#10B981" },
  { name: "Rosa", hex: "#EC4899" },
  { name: "Laranja", hex: "#F97316" },
];

export default function Settings() {
  const { user, updateSettings } = useAuth();
  
  const currentSettings = user?.settings || {
    theme: "system",
    primary_color: "#6B9E7F",
    density: "comfortable",
    font_size: "medium",
  };

  const [theme, setTheme] = useState(currentSettings.theme);
  const [primaryColor, setPrimaryColor] = useState(currentSettings.primary_color || "#6B9E7F");
  const [density, setDensity] = useState(currentSettings.density);
  const [fontSize, setFontSize] = useState(currentSettings.font_size || "medium");
  const [customColor, setCustomColor] = useState(
    COLORS.some(c => c.hex.toLowerCase() === (currentSettings.primary_color || "").toLowerCase())
      ? ""
      : currentSettings.primary_color || ""
  );
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const selectedColor = customColor || primaryColor;
      await updateSettings({
        theme,
        primary_color: selectedColor,
        density,
        font_size: fontSize,
      });
      toast.success("Configurações salvas com sucesso!");
    } catch (error) {
      console.error(error);
      toast.error("Erro ao salvar configurações.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-8 animate-in fade-in duration-300">
      <div>
        <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 dark:text-white">
          Configurações Visuais
        </h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Personalize a aparência do seu painel e otimize sua produtividade.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden">
        <div className="p-6 sm:p-8 space-y-8">
          
          {/* TEMA */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-gray-800 dark:text-white font-semibold">
              <Sun size={20} className="text-primary" />
              <h3>Tema do Sistema</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { id: "light", label: "Claro", icon: Sun, desc: "Aparência limpa e brilhante" },
                { id: "dark", label: "Escuro", icon: Moon, desc: "Fácil para os olhos no escuro" },
                { id: "system", label: "Automático", icon: Laptop, desc: "Segue o tema do seu sistema" },
              ].map(item => {
                const Icon = item.icon;
                const isSelected = theme === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setTheme(item.id as any)}
                    className={`flex flex-col items-center justify-center p-5 rounded-2xl border-2 text-center transition-all duration-200 cursor-pointer ${
                      isSelected
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-gray-100 dark:border-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/30 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    <Icon size={24} className={`mb-2 ${isSelected ? "text-primary" : "text-gray-400"}`} />
                    <span className="font-semibold text-sm">{item.label}</span>
                    <span className="text-xs text-gray-400 mt-1">{item.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* PALETA DE COR */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-gray-800 dark:text-white font-semibold">
              <Palette size={20} className="text-primary" />
              <h3>Cor de Destaque (Accent Color)</h3>
            </div>
            <div className="flex flex-wrap gap-3 items-center">
              {COLORS.map(color => {
                const isSelected = !customColor && primaryColor === color.hex;
                return (
                  <button
                    key={color.hex}
                    onClick={() => {
                      setPrimaryColor(color.hex);
                      setCustomColor("");
                    }}
                    className={`w-10 h-10 rounded-full flex items-center justify-center border-4 transition-all duration-200 cursor-pointer hover:scale-110 ${
                      isSelected ? "border-gray-900 dark:border-white shadow-lg" : "border-transparent"
                    }`}
                    style={{ backgroundColor: color.hex }}
                    title={color.name}
                  >
                    {isSelected && (
                      <span className="w-2.5 h-2.5 rounded-full bg-white shadow-sm" />
                    )}
                  </button>
                );
              })}

              <div className="flex items-center gap-2 pl-2 border-l border-gray-200 dark:border-gray-700">
                <input
                  type="color"
                  value={customColor || primaryColor}
                  onChange={(e) => {
                    setCustomColor(e.target.value);
                    setPrimaryColor(e.target.value);
                  }}
                  className="w-8 h-8 rounded-lg cursor-pointer border border-gray-300 dark:border-gray-600 overflow-hidden"
                  title="Cor personalizada"
                />
                <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Personalizada</span>
              </div>
            </div>
          </div>

          {/* DENSIDADE */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-gray-800 dark:text-white font-semibold">
              <Layout size={20} className="text-primary" />
              <h3>Densidade da Interface</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { id: "comfortable", label: "Confortável", desc: "Mais espaçamento, ideal para telas grandes" },
                { id: "compact", label: "Compacto", desc: "Mais densidade de dados, ideal para listas longas" },
              ].map(item => {
                const isSelected = density === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setDensity(item.id as any)}
                    className={`flex flex-col items-start p-5 rounded-2xl border-2 text-left transition-all duration-200 cursor-pointer ${
                      isSelected
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-gray-100 dark:border-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/30 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    <span className="font-semibold text-sm">{item.label}</span>
                    <span className="text-xs text-gray-400 mt-1">{item.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* TAMANHO DE FONTE */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-gray-800 dark:text-white font-semibold">
              <Type size={20} className="text-primary" />
              <h3>Tamanho da Fonte</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                { id: "small", label: "Pequeno (13.5px)", desc: "Maximiza exibição de textos" },
                { id: "medium", label: "Padrão (15px)", desc: "Equilíbrio padrão" },
                { id: "large", label: "Grande (17.5px)", desc: "Melhor legibilidade" },
              ].map(item => {
                const isSelected = fontSize === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setFontSize(item.id as any)}
                    className={`flex flex-col items-center justify-center p-4 rounded-2xl border-2 text-center transition-all duration-200 cursor-pointer ${
                      isSelected
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-gray-100 dark:border-gray-700 hover:border-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/30 text-gray-700 dark:text-gray-300"
                    }`}
                  >
                    <span className={`font-semibold text-sm ${item.id === "small" ? "text-xs" : item.id === "large" ? "text-base" : ""}`}>
                      {item.label}
                    </span>
                    <span className="text-xs text-gray-400 mt-1">{item.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

        </div>

        {/* BOTTOM SAVE FOOTER */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-700 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 bg-primary hover:bg-primary/95 text-white px-6 py-2.5 rounded-xl font-semibold shadow-lg shadow-primary/20 transition-all duration-200 cursor-pointer disabled:opacity-70"
          >
            <Save size={18} />
            {saving ? "Salvando..." : "Salvar Alterações"}
          </button>
        </div>
      </div>
    </div>
  );
}
