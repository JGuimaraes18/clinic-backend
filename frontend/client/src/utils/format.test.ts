import { afterEach, describe, expect, it, vi } from "vitest";

import {
  calculateAge,
  formatAgeWithBirth,
  formatCPF,
  formatCNPJ,
  formatDateBR,
  formatPhone,
} from "./format";

describe("formatCPF", () => {
  it("formata CPF valido", () => {
    expect(formatCPF("11122233344")).toBe("111.222.333-44");
  });

  it("ignora separadores ja presentes", () => {
    expect(formatCPF("111.222.333-44")).toBe("111.222.333-44");
  });

  it("devolve a entrada quando o tamanho nao e 11", () => {
    expect(formatCPF("1234567890")).toBe("1234567890");
    expect(formatCPF("")).toBe("");
  });
});

describe("formatCNPJ", () => {
  it("formata CNPJ valido", () => {
    expect(formatCNPJ("11222333000181")).toBe("11.222.333/0001-81");
  });

  it("devolve a entrada quando o tamanho nao e 14", () => {
    expect(formatCNPJ("112223330001")).toBe("112223330001");
  });
});

describe("formatPhone", () => {
  it("formata celular com 11 digitos", () => {
    expect(formatPhone("11999991234")).toBe("(11) 99999-1234");
  });

  it("formata fixo com 10 digitos", () => {
    expect(formatPhone("1133334567")).toBe("(11) 3333-4567");
  });

  it("devolve a entrada quando o tamanho nao e 10 nem 11", () => {
    expect(formatPhone("1199")).toBe("1199");
    expect(formatPhone("")).toBe("");
  });
});

describe("formatDateBR", () => {
  it("converte ISO para dia/mes/ano", () => {
    expect(formatDateBR("2024-01-15")).toBe("15/01/2024");
  });

  it("devolve string vazia para valor vazio", () => {
    expect(formatDateBR("")).toBe("");
  });
});

describe("calculateAge / formatAgeWithBirth", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("calcula idade exata no aniversario", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 5, 15, 12, 0, 0));

    expect(calculateAge("1990-06-15")).toBe(36);
    expect(formatAgeWithBirth("1990-06-15")).toBe("36 (15/06/1990)");
  });

  it("subtrai um ano quando o aniversario ainda nao aconteceu", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 5, 15, 12, 0, 0));

    expect(calculateAge("1990-07-15")).toBe(35);
    expect(calculateAge("1990-06-16")).toBe(35);
  });

  it("nao subtrai quando o aniversario ja passou no mes", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date(2026, 5, 15, 12, 0, 0));

    expect(calculateAge("1990-06-14")).toBe(36);
  });

  it("formatAgeWithBirth devolve vazio para data vazia", () => {
    expect(formatAgeWithBirth("")).toBe("");
  });
});
