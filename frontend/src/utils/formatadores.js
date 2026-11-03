// Funções de formatação usadas nas telas

export const formatarMoeda = (valor) =>
  Number(valor ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

// "2026-09-25" -> "25/09/2026"
export const formatarData = (iso) => (iso ? iso.split('-').reverse().join('/') : '')

// data de hoje no formato AAAA-MM-DD (fuso local)
export const hojeISO = () => {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

// rótulo e cor de cada situação da extração (status_extracao)
export const STATUS_DESPESA = {
  manual: { label: 'Manual', cor: 'grey-6' },
  pendente: { label: 'Pendente', cor: 'blue-grey' },
  concluida: { label: 'Extraída', cor: 'positive' },
  corrigida_manualmente: { label: 'Extraída e corrigida', cor: 'orange-8' },
  falha: { label: 'Falha na leitura', cor: 'negative' },
  recorrente: { label: 'Recorrente', cor: 'secondary' },
}

// rótulo e cor da situação de cada orçamento
export const SITUACAO_ORCAMENTO = {
  ok: { label: 'Dentro do limite', cor: 'positive' },
  alerta: { label: 'Perto do limite', cor: 'orange-8' },
  excedido: { label: 'Limite excedido', cor: 'negative' },
}

// 112.5 -> "112,5%"
export const formatarPercentual = (valor) => `${Number(valor).toLocaleString('pt-BR')}%`
