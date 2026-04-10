
import { useRouteMatch } from 'react-router-dom';
import PageHeader from '@/components/PageHeader';
import ServiceList from '@/components/ServiceList';

const ServicesPage = () => {
  const match = useRouteMatch();

  return (
    <>
      <PageHeader title="Services" />
      <ServiceList services={match.params.services} />
    </>
  );
};

export default ServicesPage;

