export function formatCPF(cpf: string) {
  const cleaned = cpf.replace(/\D/g, "");

  if (cleaned.length !== 11) return cpf;

  return cleaned.replace(
    /(\d{3})(\d{3})(\d{3})(\d{2})/,
    "$1.$2.$3-$4"
  );
}

export function formatCNPJ(cnpj: string) {
  const cleaned = cnpj.replace(/\D/g, "");

  if (cleaned.length !== 14) return cnpj;

  return cleaned.replace(
    /(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/,
    "$1.$2.$3/$4-$5"
  );
}
export function formatPhone(phone: string) {
  const cleaned = phone.replace(/\D/g, "");

  if (cleaned.length === 11) {
    return cleaned.replace(
      /(\d{2})(\d{5})(\d{4})/,
      "($1) $2-$3"
    );
  }

  if (cleaned.length === 10) {
    return cleaned.replace(
      /(\d{2})(\d{4})(\d{4})/,
      "($1) $2-$3"
    );
  }

  return phone;
}

export function formatDateBR(dateString: string) {
  if (!dateString) return "";

  const [year, month, day] = dateString.split("-");

  return `${day}/${month}/${year}`;
}

export function calculateAge(dateString: string): number {
  const birthDate = new Date(dateString);
  const today = new Date();

  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();

  if (
    monthDiff < 0 ||
    (monthDiff === 0 && today.getDate() < birthDate.getDate())
  ) {
    age--;
  }

  return age;
}

export function formatAgeWithBirth(dateString: string) {
  if (!dateString) return "";

  const age = calculateAge(dateString);
  const formattedDate = formatDateBR(dateString);

  return `${age} (${formattedDate})`;
}