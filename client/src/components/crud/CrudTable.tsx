<CrudTable
  title="Pacientes"
  fetchData={getPatients}
  createData={createPatient}
  columns={[
    { label: "Nome", render: (p) => p.full_name },
    { label: "CPF", render: (p) => formatCPF(p.cpf) },
    { label: "Email", render: (p) => p.email },
  ]}
/>