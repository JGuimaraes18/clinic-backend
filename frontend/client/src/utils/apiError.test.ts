import { describe, expect, it } from "vitest";

import { getApiErrorMessage } from "./apiError";

const FALLBACK = "Mensagem padrão de erro";

function axiosLike(data?: unknown, hasResponse = true) {
  return {
    isAxiosError: true,
    response: hasResponse ? { data } : undefined,
  };
}

describe("getApiErrorMessage", () => {
  it("usa a string retornada pelo corpo da resposta", () => {
    expect(getApiErrorMessage(axiosLike("Sessão expirada"), FALLBACK)).toBe(
      "Sessão expirada"
    );
  });

  it("monta a mensagem a partir dos campos de erro", () => {
    const error = axiosLike({ cpf: ["CPF already registered in this clinic."] });

    expect(getApiErrorMessage(error, FALLBACK)).toBe(
      "cpf: CPF already registered in this clinic."
    );
  });

  it("nao prefixa campos genericos", () => {
    const error = axiosLike({ detail: "Não encontrado." });

    expect(getApiErrorMessage(error, FALLBACK)).toBe("Não encontrado.");
  });

  it("concatena varios campos", () => {
    const error = axiosLike({
      email: ["Este campo é obrigatório."],
      phone: ["Número inválido."],
    });

    expect(getApiErrorMessage(error, FALLBACK)).toBe(
      "email: Este campo é obrigatório. phone: Número inválido."
    );
  });

  it("ignora valores vazios e nao string", () => {
    expect(getApiErrorMessage(axiosLike({ detail: "" }), FALLBACK)).toBe(
      FALLBACK
    );
    expect(getApiErrorMessage(axiosLike({ detail: 5 }), FALLBACK)).toBe(
      FALLBACK
    );
    expect(getApiErrorMessage(axiosLike([]), FALLBACK)).toBe(FALLBACK);
    expect(getApiErrorMessage(axiosLike(null), FALLBACK)).toBe(FALLBACK);
  });

  it("informa falha de conexao quando nao ha resposta", () => {
    expect(getApiErrorMessage(axiosLike(undefined, false), FALLBACK)).toBe(
      "Não foi possível conectar ao servidor. Verifique sua conexão."
    );
  });

  it("usa o fallback para erros que nao sao do axios", () => {
    expect(getApiErrorMessage(new Error("boom"), FALLBACK)).toBe(FALLBACK);
    expect(getApiErrorMessage(undefined, FALLBACK)).toBe(FALLBACK);
    expect(getApiErrorMessage("boom", FALLBACK)).toBe(FALLBACK);
  });
});
